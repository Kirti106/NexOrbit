import csv
import io
import logging
import math
import time
from datetime import datetime, timedelta, timezone
from threading import Lock

import httpx
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from ..config import get_settings
from ..models import Conjunction, GPHistory, Satellite
from sgp4.api import Satrec

logger = logging.getLogger(__name__)
CELESTRAK_URL = "https://celestrak.org/NORAD/elements/gp.php"
_sync_lock = Lock()


def _http_get(url: str, params: dict[str, str] | None = None) -> str:
    last_error: Exception | None = None
    for attempt in range(3):
        try:
            response = httpx.get(
                url,
                params=params,
                timeout=httpx.Timeout(15.0, connect=5.0),
                headers={"User-Agent": "NexOrbit/1.0"},
            )
            response.raise_for_status()
            return response.text
        except (httpx.TimeoutException, httpx.TransportError, httpx.HTTPStatusError) as exc:
            last_error = exc
            if attempt < 2:
                time.sleep(0.25 * (attempt + 1))
    raise RuntimeError("Unable to retrieve upstream data") from last_error


def fetch_tle_group(group: str = "active") -> list[tuple[str, str, str]]:
    lines = [
        line.strip()
        for line in _http_get(
            CELESTRAK_URL, {"GROUP": group, "FORMAT": "tle"}
        ).splitlines()
        if line.strip()
    ]
    records: list[tuple[str, str, str]] = []
    for index in range(0, len(lines) - 2, 3):
        name, line1, line2 = lines[index : index + 3]
        if line1.startswith("1 ") and line2.startswith("2 "):
            records.append((name, line1, line2))
    return records


def _epoch_from_tle(line1: str) -> datetime:
    year_short = int(line1[18:20])
    year = 2000 + year_short if year_short < 57 else 1900 + year_short
    day = float(line1[20:32])
    return datetime(year, 1, 1, tzinfo=timezone.utc) + timedelta(days=day - 1)


def _satellite_from_lines(name: str, line1: str, line2: str) -> tuple[int, Satrec, datetime]:
    norad_id = int(line1[2:7].strip())
    satellite = Satrec.twoline2rv(line1, line2)
    return norad_id, satellite, _epoch_from_tle(line1)


def sync_tle_group(db: Session, group: str = "active") -> tuple[int, int, bool]:
    with _sync_lock:
        newest_fetch = db.scalar(select(func.max(GPHistory.fetched_at)))
        now = datetime.now(timezone.utc)
        if newest_fetch and (now - newest_fetch).total_seconds() < 7200:
            return 0, 0, True
        records = fetch_tle_group(group)
        changed = 0
        for name, line1, line2 in records:
            try:
                norad_id, elements, epoch = _satellite_from_lines(name, line1, line2)
            except (ValueError, IndexError):
                logger.warning("Skipping malformed CelesTrak TLE record")
                continue
            satellite = db.scalar(
                select(Satellite).where(
                    or_(
                        Satellite.norad_cat_id == norad_id,
                        Satellite.norad_id == norad_id,
                    )
                )
            )
            if satellite is None:
                satellite = Satellite()
                db.add(satellite)
            satellite.norad_id = norad_id
            satellite.norad_cat_id = norad_id
            satellite.name = name[:255]
            satellite.object_name = name[:255]
            satellite.line1 = line1
            satellite.line2 = line2
            satellite.epoch = epoch.isoformat()
            satellite.source = "CelesTrak"
            satellite.updated_at = now
            satellite.object_type = satellite.object_type or "UNKNOWN"

            gp = db.scalar(
                select(GPHistory).where(
                    GPHistory.norad_cat_id == norad_id,
                    GPHistory.epoch == epoch,
                )
            )
            if gp is None:
                gp = GPHistory(norad_cat_id=norad_id, epoch=epoch)
                db.add(gp)
            gp.mean_motion = elements.no_kozai * 1440 / (2 * math.pi)
            gp.eccentricity = elements.ecco
            gp.inclination = math.degrees(elements.inclo)
            gp.ra_of_asc_node = math.degrees(elements.nodeo)
            gp.arg_of_pericenter = math.degrees(elements.argpo)
            gp.mean_anomaly = math.degrees(elements.mo)
            gp.bstar = elements.bstar
            gp.mean_motion_dot = elements.ndot
            gp.mean_motion_ddot = elements.nddot
            gp.element_set_no = elements.elnum
            gp.rev_at_epoch = elements.revnum
            gp.fetched_at = now
            changed += 1
        db.commit()
        return len(records), changed, False


def sync_conjunctions(db: Session) -> tuple[int, int]:
    source_url = get_settings().socrates_url
    if not source_url:
        raise RuntimeError(
            "SOCRATES_URL is not configured; no verified live CSV endpoint is available"
        )
    text = _http_get(source_url)
    reader = csv.DictReader(io.StringIO(text))
    now = datetime.now(timezone.utc)
    received = 0
    changed = 0
    for record in reader:
        received += 1
        try:
            id1 = int(record["NORAD_CAT_ID_1"])
            id2 = int(record["NORAD_CAT_ID_2"])
            tca = datetime.fromisoformat(record["TCA"].replace("Z", "+00:00"))
            if tca.tzinfo is None:
                tca = tca.replace(tzinfo=timezone.utc)
            tca = tca.astimezone(timezone.utc)
            distance = float(record["MIN_RANGE_KM"])
            probability = float(record["MAX_PROB"]) if record.get("MAX_PROB") else None
        except (KeyError, ValueError) as exc:
            raise RuntimeError("SOCRATES CSV has an unsupported schema") from exc
        row = db.scalar(
            select(Conjunction).where(
                Conjunction.norad_cat_id_1 == id1,
                Conjunction.norad_cat_id_2 == id2,
                Conjunction.tca == tca,
            )
        )
        if row is None:
            row = Conjunction(norad_cat_id_1=id1, norad_cat_id_2=id2, tca=tca)
            db.add(row)
        row.min_range_km = distance
        row.rel_speed_kms = (
            float(record["REL_SPEED_KMS"]) if record.get("REL_SPEED_KMS") else None
        )
        row.max_prob = probability
        row.object_name_1 = record.get("OBJECT_NAME_1")
        row.object_name_2 = record.get("OBJECT_NAME_2")
        row.is_constellation_artifact = (
            record.get("IS_CONSTELLATION_ARTIFACT", "false").lower() == "true"
        )
        row.fetched_at = now
        changed += 1
    db.commit()
    return received, changed

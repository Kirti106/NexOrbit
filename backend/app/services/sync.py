import asyncio
import csv
import io
import logging
import re
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx
from sqlalchemy.orm import Session

from ..config import Settings
from ..repositories.sync import (
    commit_sync,
    latest_gp_fetched_at,
    upsert_conjunction,
    upsert_gp_elements,
    upsert_satellite,
)
from .risk import risk_tier

logger = logging.getLogger(__name__)
CELESTRAK_GP_URL = "https://celestrak.org/NORAD/elements/gp.php"


async def _fetch(url: str, params: dict[str, str] | None = None) -> httpx.Response:
    timeout = httpx.Timeout(30, connect=5)
    last_error: Exception | None = None
    async with httpx.AsyncClient(timeout=timeout) as client:
        for attempt in range(3):
            try:
                response = await client.get(url, params=params)
                response.raise_for_status()
                return response
            except (httpx.TimeoutException, httpx.TransportError, httpx.HTTPStatusError) as exc:
                last_error = exc
                if attempt < 2:
                    await asyncio.sleep(0.5 * (2**attempt))
    if last_error:
        raise last_error
    raise RuntimeError("Remote data request did not complete")


def _utc_datetime(value: Any) -> datetime:
    parsed = value if isinstance(value, datetime) else datetime.fromisoformat(
        str(value).replace("Z", "+00:00")
    )
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


async def sync_gp(db: Session, group: str) -> dict:
    latest = latest_gp_fetched_at(db)
    now = datetime.now(timezone.utc)
    if latest and now - _utc_datetime(latest) < timedelta(hours=2):
        return {
            "source": "CelesTrak",
            "received": 0,
            "inserted_or_updated": 0,
            "skipped": True,
            "message": "Skipped: CelesTrak GP data was fetched less than two hours ago.",
        }
    response = await _fetch(CELESTRAK_GP_URL, {"GROUP": group, "FORMAT": "json"})
    records = response.json()
    if not isinstance(records, list):
        raise ValueError("CelesTrak response did not contain a GP record list")
    changed = 0
    for record in records:
        try:
            norad_id = int(record["NORAD_CAT_ID"])
            epoch = _utc_datetime(record["EPOCH"])
            name = str(record.get("OBJECT_NAME") or f"NORAD {norad_id}")[:255]
            country = record.get("COUNTRY_CODE")
            values = {
                "norad_cat_id": norad_id,
                "epoch": epoch,
                "mean_motion": _float(record.get("MEAN_MOTION")),
                "eccentricity": _float(record.get("ECCENTRICITY")),
                "inclination": _float(record.get("INCLINATION")),
                "ra_of_asc_node": _float(record.get("RA_OF_ASC_NODE")),
                "arg_of_pericenter": _float(record.get("ARG_OF_PERICENTER")),
                "mean_anomaly": _float(record.get("MEAN_ANOMALY")),
                "bstar": _float(record.get("BSTAR")),
                "mean_motion_dot": _float(record.get("MEAN_MOTION_DOT")),
                "mean_motion_ddot": _float(record.get("MEAN_MOTION_DDOT")),
                "element_set_no": _int(record.get("ELEMENT_SET_NO")),
                "rev_at_epoch": _int(record.get("REV_AT_EPOCH")),
                "fetched_at": now,
            }
            upsert_satellite(
                db,
                {
                    "norad_cat_id": norad_id,
                    "object_name": name,
                    "object_type": record.get("OBJECT_TYPE"),
                    "owner_country": country,
                    "country": country,
                    "source": "CelesTrak",
                    "updated_at": now,
                },
            )
            upsert_gp_elements(db, values)
            changed += 1
        except (KeyError, TypeError, ValueError):
            logger.warning("Skipping malformed CelesTrak GP record")
    commit_sync(db)
    return {
        "source": "CelesTrak",
        "received": len(records),
        "inserted_or_updated": changed,
        "skipped": False,
        "message": "GP catalog and orbital elements were synchronized.",
    }


async def sync_conjunctions(db: Session, settings: Settings) -> dict:
    if not settings.socrates_url:
        raise RuntimeError(
            "SOCRATES_URL is not configured; no verified live CSV endpoint is available."
        )
    response = await _fetch(settings.socrates_url)
    reader = csv.DictReader(io.StringIO(response.text))
    required = {
        "NORAD_CAT_ID_1",
        "NORAD_CAT_ID_2",
        "TCA",
        "TCA_RANGE",
        "TCA_RELATIVE_SPEED",
        "MAX_PROB",
    }
    if not reader.fieldnames or not required.issubset(reader.fieldnames):
        raise ValueError("SOCRATES response is missing required CSV columns")
    now = datetime.now(timezone.utc)
    records = list(reader)
    changed = 0
    for record in records:
        try:
            first = int(record["NORAD_CAT_ID_1"])
            second = int(record["NORAD_CAT_ID_2"])
            tca = _utc_datetime(record["TCA"])
            range_km = _float(record.get("TCA_RANGE"))
            probability = _float(record.get("MAX_PROB"))
            name_1 = record.get("OBJECT_NAME_1")
            name_2 = record.get("OBJECT_NAME_2")
            artifact = (
                range_km is not None
                and range_km <= 1.0
                and _constellation_base(name_1) != ""
                and _constellation_base(name_1) == _constellation_base(name_2)
            )
            values = {
                "object_name_1": name_1,
                "object_name_2": name_2,
                "min_range_km": range_km,
                "rel_speed_kms": _float(record.get("TCA_RELATIVE_SPEED")),
                "max_prob": probability,
                "dse_1": _float(record.get("DSE_1")),
                "dse_2": _float(record.get("DSE_2")),
                "dilution": _float(record.get("DILUTION")),
                "is_constellation_artifact": artifact,
                "risk_weight": 0.1 if artifact else 1.0,
                "risk_tier": risk_tier(probability, range_km, artifact),
                "fetched_at": now,
            }
            upsert_conjunction(
                db,
                {
                    "norad_cat_id_1": first,
                    "norad_cat_id_2": second,
                    "tca": tca,
                    **values,
                },
            )
            changed += 1
        except (KeyError, TypeError, ValueError):
            logger.warning("Skipping malformed SOCRATES row")
    commit_sync(db)
    return {
        "source": "SOCRATES",
        "received": len(records),
        "inserted_or_updated": changed,
        "skipped": False,
        "message": "SOCRATES conjunction predictions were synchronized.",
    }


def _float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    return float(value)


def _int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    return int(value)


def _constellation_base(name: str | None) -> str:
    if not name:
        return ""
    first = str(name).upper().strip().split()[0]
    return re.sub(r"[^A-Z]", "", first.split("-")[0])

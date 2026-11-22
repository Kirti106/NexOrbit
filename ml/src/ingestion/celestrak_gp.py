from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

from ..utils.storage import ensure_satellite_stubs, session_scope, upsert_gp_history
from .base import DataSource

GP_FIELDS = {
    "NORAD_CAT_ID",
    "OBJECT_NAME",
    "OBJECT_ID",
    "EPOCH",
    "MEAN_MOTION",
    "ECCENTRICITY",
    "INCLINATION",
    "RA_OF_ASC_NODE",
    "ARG_OF_PERICENTER",
    "MEAN_ANOMALY",
    "BSTAR",
    "MEAN_MOTION_DOT",
    "MEAN_MOTION_DDOT",
    "ELEMENT_SET_NO",
}


def utc_datetime(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


class CelestrakGpSource(DataSource):
    def __init__(
        self,
        *,
        base_url: str,
        group: str,
        timeout_seconds: int = 30,
        retry_attempts: int = 3,
        retry_backoff_seconds: float = 2,
        cache_ttl_seconds: int = 7200,
        user_agent: str = "NexOrbit/1.0",
        cache_dir: str | Path | None = None,
    ) -> None:
        self.base_url = base_url
        self.group = group
        self.timeout_seconds = timeout_seconds
        self.retry_attempts = retry_attempts
        self.retry_backoff_seconds = retry_backoff_seconds
        self.cache_ttl_seconds = cache_ttl_seconds
        self.user_agent = user_agent
        self.cache_dir = Path(cache_dir or "ml/data/raw")

    @classmethod
    def from_file(cls, path: str | Path) -> "CelestrakGpSource":
        source = cls(
            base_url="",
            group=Path(path).stem,
            cache_dir="ml/data/raw",
        )
        source._from_file_path = Path(path)
        return source

    def fetch(self) -> list[dict[str, Any]]:
        if hasattr(self, "_from_file_path"):
            return json.loads(self._from_file_path.read_text(encoding="utf-8-sig"))
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        cache_path = self.cache_dir / f"gp_{self.group}_{int(time.time() // 7200 * 7200)}.json"
        if cache_path.exists():
            age = time.time() - cache_path.stat().st_mtime
            if age <= self.cache_ttl_seconds:
                return json.loads(cache_path.read_text(encoding="utf-8"))

        last_error: Exception | None = None
        for attempt in range(self.retry_attempts):
            try:
                response = requests.get(
                    self.base_url,
                    params={"GROUP": self.group, "FORMAT": "json"},
                    timeout=self.timeout_seconds,
                    headers={"User-Agent": self.user_agent},
                )
                response.raise_for_status()
                data = response.json()
                if not isinstance(data, list):
                    raise ValueError("CelesTrak GP response must be a JSON list")
                cache_path.write_text(json.dumps(data), encoding="utf-8")
                return data
            except (requests.RequestException, ValueError) as exc:
                last_error = exc
                if attempt + 1 < self.retry_attempts:
                    time.sleep(self.retry_backoff_seconds * (2**attempt))
        raise RuntimeError(f"CelesTrak GP fetch failed after retries: {last_error}")

    def validate(self, data: list[dict[str, Any]]) -> bool:
        if not data:
            return True
        missing = sorted(GP_FIELDS.difference(set(data[0])))
        if missing:
            raise ValueError(f"CelesTrak GP sample is missing fields: {missing}")
        return True

    def load(self, data: list[dict[str, Any]]) -> int:
        rows = []
        satellite_stubs = []
        fetched_at = datetime.now(timezone.utc)
        for record in data:
            try:
                norad_cat_id = int(record["NORAD_CAT_ID"])
                satellite_stubs.append(
                    {
                        "norad_cat_id": norad_cat_id,
                        "object_name": str(record["OBJECT_NAME"]).strip() or None,
                    }
                )
                rows.append(
                    {
                        "norad_cat_id": norad_cat_id,
                        "epoch": utc_datetime(str(record["EPOCH"])),
                        "mean_motion": float(record["MEAN_MOTION"]),
                        "eccentricity": float(record["ECCENTRICITY"]),
                        "inclination": float(record["INCLINATION"]),
                        "ra_of_asc_node": float(record["RA_OF_ASC_NODE"]),
                        "arg_of_pericenter": float(record["ARG_OF_PERICENTER"]),
                        "mean_anomaly": float(record["MEAN_ANOMALY"]),
                        "bstar": float(record["BSTAR"]),
                        "mean_motion_dot": float(record["MEAN_MOTION_DOT"]),
                        "mean_motion_ddot": float(record.get("MEAN_MOTION_DDOT", 0.0)),
                        "element_set_no": int(record["ELEMENT_SET_NO"]) if record.get("ELEMENT_SET_NO") not in (None, "") else None,
                        "rev_at_epoch": int(record["REV_AT_EPOCH"]) if record.get("REV_AT_EPOCH") not in (None, "") else None,
                        "fetched_at": fetched_at,
                    }
                )
            except (KeyError, TypeError, ValueError) as exc:
                raise ValueError(f"Invalid CelesTrak GP record: {record}") from exc
        with session_scope() as session:
            ensure_satellite_stubs(session, satellite_stubs)
            return upsert_gp_history(session, rows)

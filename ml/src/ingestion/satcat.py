from __future__ import annotations

import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from ..utils.storage import session_scope, upsert_satellites
from .base import DataSource

SATCAT_FIELDS = {
    "NORAD_CAT_ID",
    "OBJECT_NAME",
    "OBJECT_ID",
    "OBJECT_TYPE",
    "OWNER",
    "LAUNCH_DATE",
    "DECAY_DATE",
}


def parse_optional_date(value: str | None) -> datetime | None:
    if not value:
        return None
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


class SatcatSource(DataSource):
    def __init__(self, csv_path: str | Path) -> None:
        self.csv_path = Path(csv_path)

    def fetch(self) -> list[dict[str, str]]:
        if self.csv_path.suffix.lower() == ".json":
            import json

            return json.loads(self.csv_path.read_text(encoding="utf-8-sig"))
        with self.csv_path.open("r", encoding="utf-8-sig", newline="") as source:
            return list(csv.DictReader(source))

    def validate(self, data: list[dict[str, str]]) -> bool:
        if not data:
            return True
        fields = set(data[0])
        required = SATCAT_FIELDS | ({"RCS_SIZE"} if "RCS_SIZE" in fields else {"RCS"})
        missing = sorted(required.difference(fields))
        if missing:
            raise ValueError(f"SATCAT sample is missing fields: {missing}")
        return True

    def load(self, data: list[dict[str, str]]) -> int:
        rows = []
        for record in data:
            try:
                type_code = str(record["OBJECT_TYPE"]).strip().upper()
                object_type = {
                    "PAY": "PAYLOAD",
                    "DEB": "DEBRIS",
                    "R/B": "ROCKET BODY",
                    "UNK": "UNKNOWN",
                    "UNKNOWN": "UNKNOWN",
                }.get(type_code, type_code)
                rows.append(
                    {
                        "norad_cat_id": int(record["NORAD_CAT_ID"]),
                        "object_name": record["OBJECT_NAME"].strip(),
                        "object_id": record["OBJECT_ID"].strip(),
                        "object_type": object_type if object_type else "UNKNOWN",
                        "owner_country": record["OWNER"].strip(),
                        "launch_date": parse_optional_date(record["LAUNCH_DATE"]),
                        "decay_date": parse_optional_date(record["DECAY_DATE"]),
                        "rcs_size": str(record.get("RCS_SIZE", record.get("RCS", ""))).strip(),
                        "decay_status": "DECAYED" if record["DECAY_DATE"].strip() else "IN_ORBIT",
                    }
                )
            except (KeyError, TypeError, ValueError) as exc:
                raise ValueError(f"Invalid SATCAT record: {record}") from exc
        with session_scope() as session:
            return upsert_satellites(session, rows)

from __future__ import annotations

import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ..utils.storage import session_scope, upsert_conjunctions
from .base import DataSource

SOCRATES_FIELDS = {
    "NORAD_CAT_ID_1",
    "OBJECT_NAME_1",
    "DSE_1",
    "NORAD_CAT_ID_2",
    "OBJECT_NAME_2",
    "DSE_2",
    "TCA",
    "TCA_RANGE",
    "TCA_RELATIVE_SPEED",
    "MAX_PROB",
    "DILUTION",
}


def parse_utc(value: str) -> datetime:
    text = value.strip()
    try:
        parsed = datetime.strptime(text, "%Y-%m-%d %H:%M:%S.%f")
    except ValueError:
        try:
            parsed = datetime.strptime(text, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


class SocratesSource(DataSource):
    def __init__(self, csv_path: str | Path) -> None:
        self.csv_path = Path(csv_path)

    def fetch(self) -> list[dict[str, str]]:
        with self.csv_path.open("r", encoding="utf-8-sig", newline="") as source:
            return list(csv.DictReader(source))

    def validate(self, data: list[dict[str, str]]) -> bool:
        if not data:
            return True
        missing = sorted(SOCRATES_FIELDS.difference(set(data[0])))
        if missing:
            raise ValueError(f"SOCRATES snapshot is missing fields: {missing}")
        return True

    def load(self, data: list[dict[str, str]]) -> int:
        fetched_at = datetime.now(timezone.utc)
        rows: list[dict[str, Any]] = []
        for record in data:
            try:
                id1 = int(record["NORAD_CAT_ID_1"])
                id2 = int(record["NORAD_CAT_ID_2"])
                name1 = record["OBJECT_NAME_1"].strip()
                name2 = record["OBJECT_NAME_2"].strip()
                if id1 > id2:
                    id1, id2 = id2, id1
                    name1, name2 = name2, name1
                range_km = float(record["TCA_RANGE"])
                base1 = name1.upper().split()[0].split("-")[0]
                base2 = name2.upper().split()[0].split("-")[0]
                is_artifact = range_km <= 1.0 and base1 == base2
                rows.append(
                    {
                        "norad_cat_id_1": id1,
                        "norad_cat_id_2": id2,
                        "object_name_1": name1,
                        "object_name_2": name2,
                        "tca": parse_utc(record["TCA"]),
                        "min_range_km": range_km,
                        "rel_speed_kms": float(record["TCA_RELATIVE_SPEED"]),
                        "max_prob": float(record["MAX_PROB"]),
                        "dse_1": float(record["DSE_1"]) if record.get("DSE_1") else None,
                        "dse_2": float(record["DSE_2"]) if record.get("DSE_2") else None,
                        "dilution": float(record["DILUTION"]) if record.get("DILUTION") else None,
                        "is_constellation_artifact": is_artifact,
                        "risk_weight": 0.1 if is_artifact else 1.0,
                        "fetched_at": fetched_at,
                    }
                )
            except (KeyError, TypeError, ValueError) as exc:
                raise ValueError(f"Invalid SOCRATES record: {record}") from exc
        with session_scope() as session:
            return upsert_conjunctions(session, rows)

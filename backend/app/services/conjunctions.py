import csv
import io
import json
from sqlalchemy.orm import Session

from fastapi.encoders import jsonable_encoder

from ..models.satellite import Conjunction
from ..repositories.catalog import iter_conjunctions
from ..repositories.conjunctions import get_conjunction, list_conjunctions
from .risk import risk_tier


def conjunction_item(row: Conjunction) -> dict:
    return {
        "id": row.id,
        "norad_id_1": row.norad_cat_id_1,
        "norad_id_2": row.norad_cat_id_2,
        "object_name_1": row.object_name_1,
        "object_name_2": row.object_name_2,
        "tca": row.tca,
        "min_range_km": row.min_range_km,
        "rel_speed_kms": row.rel_speed_kms,
        "max_prob": row.max_prob,
        "risk_tier": risk_tier(row.max_prob, row.min_range_km, row.is_constellation_artifact),
        "is_artifact": row.is_constellation_artifact,
        "fetched_at": row.fetched_at,
        "basis": "predicted, not observed",
    }


def search_conjunctions(db: Session, **filters) -> dict:
    total, rows = list_conjunctions(db, **filters)
    return {
        "total": total,
        "items": [conjunction_item(row) for row in rows],
        "fetched_at": max((row.fetched_at for row in rows), default=None),
        "basis": "predicted, not observed",
    }


def conjunction_details(db: Session, conjunction_id: int) -> dict | None:
    row = get_conjunction(db, conjunction_id)
    return conjunction_item(row) if row is not None else None


def stream_conjunction_export(
    db: Session,
    *,
    format: str,
    risk_tier: str | None,
    severity: str | None,
    tca_from,
    tca_to,
    norad_id: int | None,
    include_artifacts: bool,
    limit: int,
    offset: int,
):
    rows = iter_conjunctions(
        db,
        risk_tier=risk_tier,
        severity=severity,
        tca_from=tca_from,
        tca_to=tca_to,
        norad_id=norad_id,
        include_artifacts=include_artifacts,
        limit=limit,
        offset=offset,
    )
    if format == "json":
        yield from _json_export(rows)
    else:
        yield from _csv_export(rows)


def _json_export(rows):
    yield "["
    first = True
    for row in rows:
        item = json.dumps(
            jsonable_encoder(conjunction_item(row)),
            separators=(",", ":"),
        )
        yield ("" if first else ",") + item
        first = False
    yield "]"


def _csv_export(rows):
    fields = (
        "id",
        "norad_id_1",
        "norad_id_2",
        "object_name_1",
        "object_name_2",
        "tca",
        "min_range_km",
        "rel_speed_kms",
        "max_prob",
        "risk_tier",
        "is_artifact",
        "fetched_at",
        "basis",
    )
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(fields)
    yield buffer.getvalue()
    buffer.seek(0)
    buffer.truncate(0)
    for row in rows:
        writer.writerow(conjunction_item(row)[field] for field in fields)
        yield buffer.getvalue()
        buffer.seek(0)
        buffer.truncate(0)

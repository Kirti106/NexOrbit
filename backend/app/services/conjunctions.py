from datetime import datetime
from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from ..models import Conjunction
from .risk import risk_tier, tier_filter


def list_conjunctions(
    db: Session,
    *,
    risk: str | None,
    tca_from: datetime | None,
    tca_to: datetime | None,
    norad_id: int | None,
    include_artifacts: bool,
    limit: int,
    offset: int,
) -> dict[str, Any]:
    statement = select(Conjunction)
    if not include_artifacts:
        statement = statement.where(Conjunction.is_constellation_artifact.is_(False))
    if tca_from is not None:
        statement = statement.where(Conjunction.tca >= tca_from)
    if tca_to is not None:
        statement = statement.where(Conjunction.tca <= tca_to)
    if norad_id is not None:
        statement = statement.where(
            or_(
                Conjunction.norad_cat_id_1 == norad_id,
                Conjunction.norad_cat_id_2 == norad_id,
            )
        )
    if risk:
        statement = statement.where(tier_filter(risk))
    total = db.scalar(select(func.count()).select_from(statement.subquery())) or 0
    rows = db.scalars(
        statement.order_by(Conjunction.tca.asc(), Conjunction.id.asc())
        .offset(offset)
        .limit(limit)
    ).all()
    items = [
        {
            "id": row.id,
            "norad_id_1": row.norad_cat_id_1,
            "norad_id_2": row.norad_cat_id_2,
            "object_name_1": row.object_name_1,
            "object_name_2": row.object_name_2,
            "tca": row.tca,
            "min_range_km": row.min_range_km,
            "rel_speed_kms": row.rel_speed_kms,
            "max_prob": row.max_prob,
            "risk_tier": risk_tier(
                row.max_prob, row.min_range_km, row.is_constellation_artifact
            ),
            "is_artifact": row.is_constellation_artifact,
            "fetched_at": row.fetched_at,
        }
        for row in rows
    ]
    newest = db.scalar(select(func.max(Conjunction.fetched_at)))
    return {
        "total": int(total),
        "basis": "predicted, not observed",
        "fetched_at": newest,
        "items": items,
    }


def conjunction_detail(db: Session, conjunction_id: int) -> dict[str, Any] | None:
    row = db.get(Conjunction, conjunction_id)
    if row is None:
        return None
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
        "risk_tier": risk_tier(
            row.max_prob, row.min_range_km, row.is_constellation_artifact
        ),
        "is_artifact": row.is_constellation_artifact,
        "fetched_at": row.fetched_at,
    }

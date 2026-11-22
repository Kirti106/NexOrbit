from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..models import Conjunction, GPHistory, Satellite
from .risk import risk_tier, tier_filter

_PERIOD_DAYS = {"7D": 7, "30D": 30, "90D": 90, "1Y": 365}


def _orbit_class(mean_motion: float | None) -> str | None:
    if mean_motion is None or mean_motion <= 0:
        return None
    if mean_motion > 11.25:
        return "LEO"
    if mean_motion > 1.5:
        return "MEO"
    return "GEO"


def _aggregates(db: Session) -> tuple[dict[str, int], dict[str, int], dict[str, datetime | None]]:
    types = db.execute(
        select(func.coalesce(Satellite.object_type, "UNKNOWN"), func.count())
        .group_by(Satellite.object_type)
    ).all()
    by_type = {str(kind).upper(): int(count) for kind, count in types}
    latest_epoch = (
        select(GPHistory.norad_cat_id, func.max(GPHistory.epoch).label("epoch"))
        .group_by(GPHistory.norad_cat_id)
        .subquery()
    )
    latest_rows = db.execute(
        select(GPHistory.mean_motion)
        .join(
            latest_epoch,
            (GPHistory.norad_cat_id == latest_epoch.c.norad_cat_id)
            & (GPHistory.epoch == latest_epoch.c.epoch),
        )
    ).scalars()
    by_orbit: dict[str, int] = {}
    for mean_motion in latest_rows:
        orbit = _orbit_class(mean_motion)
        if orbit:
            by_orbit[orbit] = by_orbit.get(orbit, 0) + 1
    freshness = {
        "gp_fetched_at": db.scalar(select(func.max(GPHistory.fetched_at))),
        "conjunctions_fetched_at": db.scalar(select(func.max(Conjunction.fetched_at))),
    }
    return by_type, by_orbit, freshness


def stats(db: Session) -> dict[str, Any]:
    by_type, by_orbit, freshness = _aggregates(db)
    total = sum(by_type.values())
    conjunction_count = db.scalar(select(func.count()).select_from(Conjunction))
    high_risk_count = db.scalar(
        select(func.count()).select_from(Conjunction).where(tier_filter("high"))
    )
    reason = None
    if not total:
        reason = "Satellite catalogue has no records."
    return {
        "total_satellites": total,
        "satellites_by_object_type": by_type,
        "satellites_by_orbit_class": by_orbit,
        "conjunction_count": int(conjunction_count or 0),
        "high_risk_conjunctions": int(high_risk_count or 0),
        "data_freshness": freshness,
        "reason": reason,
    }


def analytics(db: Session, period: str) -> dict[str, Any]:
    by_type, by_orbit, freshness = _aggregates(db)
    start = datetime.now(timezone.utc) - timedelta(days=_PERIOD_DAYS[period])
    rows = db.scalars(
        select(Conjunction).where(Conjunction.tca >= start).order_by(Conjunction.tca)
    ).all()
    daily: dict[tuple[datetime, str], int] = {}
    for row in rows:
        day = row.tca.replace(hour=0, minute=0, second=0, microsecond=0)
        tier = risk_tier(row.max_prob, row.min_range_km, row.is_constellation_artifact)
        daily[(day, tier)] = daily.get((day, tier), 0) + 1
    reason = None
    if not by_type:
        reason = "Satellite catalogue has no records."
    elif not rows:
        reason = f"No conjunction records are available for period {period}."
    return {
        "period": period,
        "satellites_by_object_type": by_type or None,
        "satellites_by_orbit_class": by_orbit or None,
        "conjunctions_per_day": [
            {"date": day, "risk_tier": tier, "count": count}
            for (day, tier), count in sorted(daily.items())
        ] if rows else None,
        "data_freshness": freshness,
        "reason": reason,
    }

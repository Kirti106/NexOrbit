from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..models.satellite import Conjunction, GPHistory, Satellite
from .satellites import orbit_class


def catalog_aggregates(db: Session) -> tuple[int, dict[str, int], dict[str, int]]:
    types_rows = db.execute(
        select(Satellite.object_type, func.count()).group_by(Satellite.object_type)
    ).all()
    by_type = {(kind or "UNKNOWN"): count for kind, count in types_rows}
    latest = (
        select(
            GPHistory.norad_cat_id,
            GPHistory.mean_motion,
            func.row_number()
            .over(
                partition_by=GPHistory.norad_cat_id,
                order_by=GPHistory.epoch.desc(),
            )
            .label("rn"),
        )
        .subquery()
    )
    orbit_rows = db.execute(
        select(latest.c.mean_motion).where(latest.c.rn == 1)
    ).scalars()
    by_orbit = {"LEO": 0, "MEO": 0, "GEO": 0}
    for mean_motion in orbit_rows:
        category = orbit_class(mean_motion)
        if category:
            by_orbit[category] += 1
    return sum(by_type.values()), by_type, by_orbit


def statistics_data(db: Session) -> dict:
    total, by_type, by_orbit = catalog_aggregates(db)
    conjunction_count = db.scalar(select(func.count()).select_from(Conjunction))
    high_count = db.scalar(
        select(func.count()).select_from(Conjunction).where(
            Conjunction.is_constellation_artifact.is_(False),
            (
                (func.coalesce(Conjunction.max_prob, 0) >= 1e-3)
                | (
                    (func.coalesce(Conjunction.max_prob, 0) >= 1e-5)
                    & (Conjunction.min_range_km <= 50)
                )
            ),
        )
    )
    return {
        "total": total,
        "by_type": by_type,
        "by_orbit": by_orbit,
        "conjunction_count": conjunction_count,
        "high_count": high_count,
        "gp_fresh": db.scalar(select(func.max(GPHistory.fetched_at))),
        "conjunction_fresh": db.scalar(select(func.max(Conjunction.fetched_at))),
    }


def conjunction_daily_data(db: Session, since: datetime) -> list:
    query = (
        select(
            func.date(Conjunction.tca).label("day"),
            func.count().label("count"),
            Conjunction.max_prob,
            Conjunction.min_range_km,
            Conjunction.is_constellation_artifact,
        )
        .where(Conjunction.tca >= since)
        .group_by(
            func.date(Conjunction.tca),
            Conjunction.max_prob,
            Conjunction.min_range_km,
            Conjunction.is_constellation_artifact,
        )
    )
    return db.execute(query).all()

from datetime import datetime

from sqlalchemy import case, func, or_, select
from sqlalchemy.orm import Session

from ..models.satellite import Conjunction, GPHistory
from ..services.risk import risk_tier
from . import analytics
from .conjunctions import list_conjunctions as _list_conjunctions
from .conjunctions import iter_conjunctions as _iter_conjunctions
from .conjunctions import severity_expression
from .satellites import get_satellite as _get_satellite
from .satellites import list_satellites as _list_satellites


def list_satellites(
    db: Session,
    *,
    q: str | None = None,
    object_type: str | None = None,
    orbit_class: str | None = None,
    country: str | None = None,
    sort: str = "name",
    limit: int = 100,
    offset: int = 0,
):
    return _list_satellites(
        db,
        q=q,
        object_type=object_type,
        requested_orbit=orbit_class,
        country=country,
        sort=sort,
        limit=limit,
        offset=offset,
    )


def get_satellite(db: Session, norad_id: int):
    return _get_satellite(db, norad_id)


def list_conjunctions(
    db: Session,
    *,
    risk_tier: str | None = None,
    severity: str | None = None,
    tca_from: datetime | None = None,
    tca_to: datetime | None = None,
    norad_id: int | None = None,
    include_artifacts: bool = False,
    limit: int = 100,
    offset: int = 0,
):
    return _list_conjunctions(
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


def iter_conjunctions(db: Session, **filters):
    yield from _iter_conjunctions(db, **filters)


def severity_counts(
    db: Session,
    *,
    tca_from: datetime | None = None,
    tca_to: datetime | None = None,
    include_artifacts: bool = True,
) -> dict[str, int]:
    severity = severity_expression()
    statement = select(severity, func.count()).select_from(Conjunction)
    if tca_from is not None:
        statement = statement.where(Conjunction.tca >= tca_from)
    if tca_to is not None:
        statement = statement.where(Conjunction.tca <= tca_to)
    if not include_artifacts:
        statement = statement.where(Conjunction.is_constellation_artifact.is_(False))
    return {name: count for name, count in db.execute(statement.group_by(severity))}


def conjunctions_per_day(db: Session, since: datetime) -> list[dict]:
    grouped: dict[datetime, dict[str, int]] = {}
    for day, count, probability, distance, is_artifact in analytics.conjunction_daily_data(
        db, since
    ):
        tiers = grouped.setdefault(day, {"low": 0, "medium": 0, "high": 0})
        tiers[risk_tier(probability, distance, is_artifact)] += count
    return [
        {
            "day": day,
            "count": sum(tiers.values()),
            "by_risk_tier": tiers,
        }
        for day, tiers in sorted(grouped.items())
    ]


def stats_snapshot(db: Session) -> dict:
    return analytics.statistics_data(db)


def orbit_class_counts(db: Session) -> dict[str, int]:
    return analytics.catalog_aggregates(db)[2]


def list_gp_history(db: Session, norad_id: int, limit: int) -> list[GPHistory]:
    return db.scalars(
        select(GPHistory)
        .where(GPHistory.norad_cat_id == norad_id)
        .order_by(GPHistory.epoch.desc())
        .limit(limit)
    ).all()


def meta_snapshot(db: Session) -> dict[str, datetime | None]:
    return {
        "gp_history_fetched_at": db.scalar(select(func.max(GPHistory.fetched_at))),
        "conjunctions_fetched_at": db.scalar(
            select(func.max(Conjunction.fetched_at))
        ),
    }


def conjunction_summary_counts(
    db: Session,
    *,
    tca_from: datetime | None = None,
    tca_to: datetime | None = None,
) -> dict[str, int | dict[str, int]]:
    probability = func.coalesce(Conjunction.max_prob, 0)
    tier = case(
        (Conjunction.is_constellation_artifact.is_(True), "low"),
        (
            or_(
                probability >= 1e-3,
                (probability >= 1e-5) & (Conjunction.min_range_km <= 50),
            ),
            "high",
        ),
        (probability >= 1e-5, "medium"),
        else_="low",
    )
    severity = severity_expression()
    statement = select(tier, severity, func.count()).select_from(Conjunction)
    if tca_from is not None:
        statement = statement.where(Conjunction.tca >= tca_from)
    if tca_to is not None:
        statement = statement.where(Conjunction.tca <= tca_to)

    by_risk_tier = {"low": 0, "medium": 0, "high": 0}
    by_severity = {"critical": 0, "high": 0, "medium": 0, "low": 0, "unknown": 0}
    total = 0
    for risk, distance_severity, count in db.execute(
        statement.group_by(tier, severity)
    ):
        total += count
        by_risk_tier[risk] += count
        by_severity[distance_severity] += count
    return {
        "total": total,
        "by_risk_tier": by_risk_tier,
        "by_severity": by_severity,
    }

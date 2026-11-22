from datetime import datetime

from sqlalchemy import and_, case, func, or_, select
from sqlalchemy.orm import Session

from ..models.satellite import Conjunction


def get_conjunction(db: Session, conjunction_id: int) -> Conjunction | None:
    return db.scalar(select(Conjunction).where(Conjunction.id == conjunction_id))


def _tier_condition(tier: str):
    p = func.coalesce(Conjunction.max_prob, 0)
    if tier == "high":
        return and_(
            Conjunction.is_constellation_artifact.is_(False),
            or_(p >= 1e-3, and_(p >= 1e-5, Conjunction.min_range_km <= 50)),
        )
    if tier == "medium":
        return and_(
            Conjunction.is_constellation_artifact.is_(False),
            p >= 1e-5,
            p < 1e-3,
            or_(Conjunction.min_range_km > 50, Conjunction.min_range_km.is_(None)),
        )
    return or_(
        Conjunction.is_constellation_artifact.is_(True),
        p < 1e-5,
        and_(p >= 1e-5, p < 1e-3, Conjunction.min_range_km <= 50),
    )


def severity_expression():
    return case(
        (Conjunction.min_range_km <= 1, "critical"),
        (Conjunction.min_range_km <= 10, "high"),
        (Conjunction.min_range_km <= 50, "medium"),
        (Conjunction.min_range_km.is_not(None), "low"),
        else_="unknown",
    )


def list_conjunctions(
    db: Session,
    *,
    risk_tier: str | None,
    severity: str | None = None,
    tca_from: datetime | None,
    tca_to: datetime | None,
    norad_id: int | None,
    include_artifacts: bool,
    limit: int,
    offset: int,
):
    statement = select(Conjunction)
    count_statement = select(func.count()).select_from(Conjunction)
    filters = _conjunction_filters(
        risk_tier=risk_tier,
        severity=severity,
        tca_from=tca_from,
        tca_to=tca_to,
        norad_id=norad_id,
        include_artifacts=include_artifacts,
    )
    if filters:
        statement = statement.where(*filters)
        count_statement = count_statement.where(*filters)
    total = db.scalar(count_statement) or 0
    rows = db.scalars(
        statement.order_by(Conjunction.tca.asc(), Conjunction.min_range_km.asc())
        .offset(offset)
        .limit(limit)
    ).all()
    return total, rows


def iter_conjunctions(
    db: Session,
    *,
    risk_tier: str | None,
    severity: str | None,
    tca_from: datetime | None,
    tca_to: datetime | None,
    norad_id: int | None,
    include_artifacts: bool,
    limit: int,
    offset: int,
):
    statement = select(Conjunction)
    filters = _conjunction_filters(
        risk_tier=risk_tier,
        severity=severity,
        tca_from=tca_from,
        tca_to=tca_to,
        norad_id=norad_id,
        include_artifacts=include_artifacts,
    )
    if filters:
        statement = statement.where(*filters)
    result = db.scalars(
        statement.order_by(Conjunction.tca.asc(), Conjunction.min_range_km.asc())
        .offset(offset)
        .limit(limit)
        .execution_options(stream_results=True, yield_per=500)
    )
    yield from result


def _conjunction_filters(
    *,
    risk_tier: str | None,
    severity: str | None,
    tca_from: datetime | None,
    tca_to: datetime | None,
    norad_id: int | None,
    include_artifacts: bool,
):
    filters = []
    if risk_tier:
        filters.append(_tier_condition(risk_tier))
    if severity:
        filters.append(severity_expression() == severity)
    if tca_from:
        filters.append(Conjunction.tca >= tca_from)
    if tca_to:
        filters.append(Conjunction.tca <= tca_to)
    if norad_id is not None:
        filters.append(
            or_(
                Conjunction.norad_cat_id_1 == norad_id,
                Conjunction.norad_cat_id_2 == norad_id,
            )
        )
    if not include_artifacts:
        filters.append(Conjunction.is_constellation_artifact.is_(False))
    return filters

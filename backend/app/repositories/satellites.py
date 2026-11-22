from sqlalchemy import String, cast, func, or_, select
from sqlalchemy.orm import Session

from ..models import GPHistory, Satellite


def list_satellites(
    db: Session,
    *,
    q: str | None,
    object_type: str | None,
    country: str | None,
    orbit_class: str | None,
    sort: str,
    limit: int,
    offset: int,
) -> tuple[int, list[Satellite]]:
    statement = select(Satellite)
    if q:
        match = f"%{q}%"
        statement = statement.where(
            or_(
                Satellite.object_name.ilike(match),
                cast(Satellite.norad_cat_id, String).ilike(match),
            )
        )
    if object_type:
        statement = statement.where(
            func.lower(Satellite.object_type) == object_type.lower()
        )
    if country:
        statement = statement.where(
            func.lower(func.coalesce(Satellite.country, Satellite.owner_country))
            == country.lower()
        )
    if orbit_class:
        latest = (
            select(GPHistory.norad_cat_id, func.max(GPHistory.epoch).label("epoch"))
            .group_by(GPHistory.norad_cat_id)
            .subquery()
        )
        motion = (
            select(GPHistory.mean_motion)
            .join(
                latest,
                (GPHistory.norad_cat_id == latest.c.norad_cat_id)
                & (GPHistory.epoch == latest.c.epoch),
            )
            .where(
                GPHistory.norad_cat_id
                == Satellite.norad_cat_id
            )
            .limit(1)
            .scalar_subquery()
        )
        boundaries = {
            "LEO": motion > 11.25,
            "MEO": (motion <= 11.25) & (motion > 1.5),
            "GEO": motion <= 1.5,
        }
        statement = statement.where(boundaries[orbit_class])
    total = db.scalar(select(func.count()).select_from(statement.subquery())) or 0
    statement = statement.order_by(
        Satellite.object_name.desc()
        if sort == "name_desc"
        else Satellite.object_name.asc()
    )
    items = list(db.scalars(statement.offset(offset).limit(limit)).all())
    return int(total), items


def get_satellite(db: Session, norad_id: int) -> Satellite | None:
    return db.scalar(
        select(Satellite).where(Satellite.norad_cat_id == norad_id)
    )


def latest_elements(db: Session, norad_id: int) -> GPHistory | None:
    return db.scalar(
        select(GPHistory)
        .where(GPHistory.norad_cat_id == norad_id)
        .order_by(GPHistory.epoch.desc())
        .limit(1)
    )

import math
from sqlalchemy import String, cast, func, or_, select
from sqlalchemy.orm import Session

from ..models.satellite import GPHistory, Satellite

EARTH_RADIUS_KM = 6378.137
EARTH_MU_KM3_S2 = 398600.4418


def altitude_from_mean_motion(mean_motion: float | None) -> float | None:
    if mean_motion is None or mean_motion <= 0:
        return None
    angular_velocity = mean_motion * 2 * math.pi / 86400
    semi_major_axis = (EARTH_MU_KM3_S2 / angular_velocity**2) ** (1 / 3)
    return semi_major_axis - EARTH_RADIUS_KM


def orbit_class(mean_motion: float | None) -> str | None:
    altitude = altitude_from_mean_motion(mean_motion)
    if altitude is None:
        return None
    if altitude < 2000:
        return "LEO"
    if altitude < 35786:
        return "MEO"
    return "GEO"


def list_satellites(
    db: Session,
    *,
    q: str | None,
    object_type: str | None,
    requested_orbit: str | None,
    country: str | None,
    sort: str,
    limit: int,
    offset: int,
):
    latest = (
        select(
            GPHistory.norad_cat_id.label("norad_cat_id"),
            GPHistory.epoch.label("epoch"),
            GPHistory.mean_motion.label("mean_motion"),
            GPHistory.eccentricity.label("eccentricity"),
            GPHistory.inclination.label("inclination"),
            func.row_number()
            .over(
                partition_by=GPHistory.norad_cat_id,
                order_by=GPHistory.epoch.desc(),
            )
            .label("row_number"),
        )
        .subquery()
    )
    statement = select(
        Satellite,
        latest.c.epoch,
        latest.c.mean_motion,
        latest.c.eccentricity,
        latest.c.inclination,
    ).outerjoin(
        latest,
        (latest.c.norad_cat_id == Satellite.norad_cat_id)
        & (latest.c.row_number == 1),
    )
    count_statement = select(func.count(func.distinct(Satellite.norad_cat_id))).select_from(
        Satellite
    ).outerjoin(
        latest,
        (latest.c.norad_cat_id == Satellite.norad_cat_id)
        & (latest.c.row_number == 1),
    )
    filters = []
    if q:
        pattern = f"%{q}%"
        filters.append(
            or_(
                Satellite.object_name.ilike(pattern),
                cast(Satellite.norad_cat_id, String).ilike(pattern),
            )
        )
    if object_type:
        filters.append(Satellite.object_type.ilike(object_type))
    if country:
        filters.append(Satellite.owner_country.ilike(country))
    if requested_orbit == "LEO":
        filters.append(latest.c.mean_motion > _mean_motion_for_altitude(2000))
    elif requested_orbit == "MEO":
        filters.extend(
            [
                latest.c.mean_motion <= _mean_motion_for_altitude(2000),
                latest.c.mean_motion > _mean_motion_for_altitude(35786),
            ]
        )
    elif requested_orbit == "GEO":
        filters.append(latest.c.mean_motion <= _mean_motion_for_altitude(35786))
    if filters:
        statement = statement.where(*filters)
        count_statement = count_statement.where(*filters)

    ordering = {
        "name": Satellite.object_name.asc(),
        "-name": Satellite.object_name.desc(),
        "norad_id": Satellite.norad_cat_id.asc(),
        "-norad_id": Satellite.norad_cat_id.desc(),
    }[sort]
    total = db.scalar(count_statement) or 0
    rows = db.execute(
        statement.order_by(ordering).offset(offset).limit(limit)
    ).all()
    return total, rows


def get_satellite(db: Session, norad_id: int):
    satellite = db.scalar(
        select(Satellite).where(Satellite.norad_cat_id == norad_id)
    )
    if satellite is None:
        return None, None
    latest = db.execute(
        select(GPHistory)
        .where(GPHistory.norad_cat_id == norad_id)
        .order_by(GPHistory.epoch.desc())
        .limit(1)
    ).scalar_one_or_none()
    return satellite, latest


def _mean_motion_for_altitude(altitude_km: float) -> float:
    semi_major_axis = EARTH_RADIUS_KM + altitude_km
    period_minutes = 2 * math.pi * math.sqrt(
        semi_major_axis**3 / EARTH_MU_KM3_S2
    ) / 60
    return 1440 / period_minutes

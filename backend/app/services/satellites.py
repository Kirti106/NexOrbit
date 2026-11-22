from datetime import datetime

from sqlalchemy.orm import Session

from ..repositories import catalog
from ..repositories.satellites import (
    EARTH_RADIUS_KM,
    EARTH_MU_KM3_S2,
    list_satellites,
    orbit_class,
)
from .conjunctions import conjunction_item


def satellite_item(satellite, elements=None) -> dict:
    return _format_satellite(
        satellite,
        elements.epoch if elements else None,
        elements.mean_motion if elements else None,
        elements.eccentricity if elements else None,
        elements.inclination if elements else None,
    )


def _format_satellite(
    satellite,
    epoch,
    mean_motion: float | None,
    eccentricity: float | None,
    inclination: float | None,
) -> dict:
    semi_major_axis = None
    if mean_motion and mean_motion > 0:
        angular_velocity = mean_motion * 2 * 3.141592653589793 / 86400
        semi_major_axis = (EARTH_MU_KM3_S2 / angular_velocity**2) ** (1 / 3)
    perigee = (
        semi_major_axis * (1 - eccentricity) - EARTH_RADIUS_KM
        if semi_major_axis is not None and eccentricity is not None
        else None
    )
    apogee = (
        semi_major_axis * (1 + eccentricity) - EARTH_RADIUS_KM
        if semi_major_axis is not None and eccentricity is not None
        else None
    )
    return {
        "norad_id": satellite.norad_cat_id,
        "name": satellite.object_name,
        "object_type": satellite.object_type,
        "country": satellite.owner_country,
        "orbit_class": orbit_class(mean_motion),
        "inclination": inclination,
        "eccentricity": eccentricity,
        "period_minutes": 1440 / mean_motion if mean_motion else None,
        "apogee_km": apogee,
        "perigee_km": perigee,
        "launch_date": satellite.launch_date,
        "status": satellite.status,
        "epoch": epoch,
    }


def search_satellites(
    db: Session,
    *,
    q: str | None,
    object_type: str | None,
    orbit: str | None,
    country: str | None,
    sort: str,
    limit: int,
    offset: int,
) -> dict:
    total, rows = list_satellites(
        db,
        q=q,
        object_type=object_type,
        requested_orbit=orbit,
        country=country,
        sort=sort,
        limit=limit,
        offset=offset,
    )
    return {
        "total": total,
        "items": [
            _format_satellite(satellite, epoch, motion, ecc, inclination)
            for satellite, epoch, motion, ecc, inclination in rows
        ],
    }


def satellite_history(db: Session, norad_id: int, limit: int) -> dict | None:
    satellite, _latest = catalog.get_satellite(db, norad_id)
    if satellite is None:
        return None
    rows = catalog.list_gp_history(db, norad_id, limit)
    return {
        "norad_id": norad_id,
        "items": [
            {
                "epoch": row.epoch,
                "mean_motion": row.mean_motion,
                "eccentricity": row.eccentricity,
                "inclination": row.inclination,
                "bstar": row.bstar,
            }
            for row in rows
        ],
    }


def satellite_conjunctions(
    db: Session,
    norad_id: int,
    *,
    risk_tier: str | None,
    severity: str | None,
    tca_from: datetime | None,
    tca_to: datetime | None,
    include_artifacts: bool,
    limit: int,
    offset: int,
) -> dict | None:
    satellite, _latest = catalog.get_satellite(db, norad_id)
    if satellite is None:
        return None
    total, rows = catalog.list_conjunctions(
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
    return {
        "total": total,
        "items": [conjunction_item(row) for row in rows],
        "fetched_at": max((row.fetched_at for row in rows), default=None),
        "basis": "predicted, not observed",
    }

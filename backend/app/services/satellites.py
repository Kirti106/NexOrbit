import math
from typing import Any

from sqlalchemy.orm import Session

from ..models import GPHistory, Satellite
from ..repositories.satellites import (
    get_satellite,
    latest_elements,
    list_satellites,
)

EARTH_RADIUS_KM = 6378.137


def _norad_id(satellite: Satellite) -> int:
    value = satellite.norad_cat_id
    if value is None:
        raise ValueError("Satellite record has no NORAD identifier")
    return value


def _name(satellite: Satellite) -> str:
    return satellite.object_name or ""


def _orbit_class(elements: GPHistory | None) -> str | None:
    if elements is None or elements.mean_motion is None:
        return None
    if elements.mean_motion > 11.25:
        return "LEO"
    if elements.mean_motion > 1.5:
        return "MEO"
    return "GEO"


def search_satellites(
    db: Session,
    *,
    q: str | None,
    object_type: str | None,
    orbit_class: str | None,
    country: str | None,
    sort: str,
    limit: int,
    offset: int,
) -> dict[str, Any]:
    total, rows = list_satellites(
        db,
        q=q,
        object_type=object_type,
        orbit_class=orbit_class,
        country=country,
        sort=sort,
        limit=limit,
        offset=offset,
    )
    return {
        "total": total,
        "items": [
            {
                "norad_id": _norad_id(row),
                "name": _name(row),
                "object_type": row.object_type,
                "country": row.owner_country or row.country,
                "orbit_class": _orbit_class(latest_elements(db, _norad_id(row))),
                "updated_at": row.updated_at,
            }
            for row in rows
        ],
    }


def satellite_detail(db: Session, norad_id: int) -> dict[str, Any] | None:
    satellite = get_satellite(db, norad_id)
    if satellite is None:
        return None
    elements = latest_elements(db, norad_id)
    orbital = None
    if elements is not None:
        mean_motion = elements.mean_motion
        semimajor_axis = (
            (398600.4418 / ((mean_motion * 2 * math.pi / 86400) ** 2)) ** (1 / 3)
            if mean_motion and mean_motion > 0
            else None
        )
        eccentricity = elements.eccentricity
        orbital = {
            "inclination": elements.inclination,
            "eccentricity": eccentricity,
            "period_minutes": 1440 / mean_motion if mean_motion and mean_motion > 0 else None,
            "apogee_km": (
                semimajor_axis * (1 + eccentricity) - EARTH_RADIUS_KM
                if semimajor_axis is not None and eccentricity is not None
                else None
            ),
            "perigee_km": (
                semimajor_axis * (1 - eccentricity) - EARTH_RADIUS_KM
                if semimajor_axis is not None and eccentricity is not None
                else None
            ),
            "epoch": elements.epoch,
        }
    return {
        "norad_id": _norad_id(satellite),
        "name": _name(satellite),
        "object_type": satellite.object_type,
        "country": satellite.owner_country or satellite.country,
        "orbit_class": _orbit_class(elements),
        "updated_at": satellite.updated_at,
        "launch_date": satellite.launch_date,
        "decay_date": satellite.decay_date,
        "mission_info": {
            "object_id": satellite.object_id,
            "rcs_size": satellite.rcs_size,
            "decay_status": satellite.decay_status,
            "source": satellite.source,
        },
        "latest_orbital_elements": orbital,
    }

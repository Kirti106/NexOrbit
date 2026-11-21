from __future__ import annotations

from datetime import datetime, timedelta, timezone
from math import sqrt
from typing import Iterable

from sgp4.api import Satrec, jday
from sgp4.omm import initialize
from sgp4.exporter import export_tle
from skyfield.api import EarthSatellite, load, wgs84

from ..utils.storage import create_database_engine
from sqlalchemy import text

EARTH_MU_KM3_S2 = 398600.4418


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def satrec_from_gp(record: dict) -> Satrec:
    def get(*names, default=None):
        for name in names:
            if name in record:
                return record[name]
        return default

    epoch_value = get("EPOCH", "epoch")
    if hasattr(epoch_value, "strftime"):
        epoch_text = epoch_value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")
    else:
        parsed_epoch = datetime.fromisoformat(str(epoch_value).replace("Z", "+00:00"))
        epoch_text = parsed_epoch.astimezone(timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%S.%f"
        )
    fields = {
        "NORAD_CAT_ID": str(get("NORAD_CAT_ID", "norad_cat_id")),
        "OBJECT_ID": str(get("OBJECT_ID", "object_id", default="00000A")),
        "CLASSIFICATION_TYPE": str(get("CLASSIFICATION_TYPE", "classification_type", default="U")),
        "EPHEMERIS_TYPE": str(get("EPHEMERIS_TYPE", "ephemeris_type", default=0)),
        "EPOCH": epoch_text,
        "MEAN_MOTION": float(get("MEAN_MOTION", "mean_motion")),
        "ECCENTRICITY": float(get("ECCENTRICITY", "eccentricity")),
        "INCLINATION": float(get("INCLINATION", "inclination")),
        "RA_OF_ASC_NODE": float(get("RA_OF_ASC_NODE", "ra_of_asc_node")),
        "ARG_OF_PERICENTER": float(get("ARG_OF_PERICENTER", "arg_of_pericenter")),
        "MEAN_ANOMALY": float(get("MEAN_ANOMALY", "mean_anomaly")),
        "BSTAR": float(get("BSTAR", "bstar")),
        "MEAN_MOTION_DOT": float(get("MEAN_MOTION_DOT", "mean_motion_dot")),
        "MEAN_MOTION_DDOT": float(get("MEAN_MOTION_DDOT", "mean_motion_ddot", default=0.0)),
        "ELEMENT_SET_NO": int(get("ELEMENT_SET_NO", "element_set_no", default=0)),
        "REV_AT_EPOCH": int(get("REV_AT_EPOCH", "rev_at_epoch", default=0)),
    }
    satellite = Satrec()
    initialize(satellite, fields)
    return satellite


def satrec_from_database(norad_id: int, epoch: datetime | None = None) -> Satrec:
    engine = create_database_engine()
    where_epoch = "AND epoch = :epoch" if epoch is not None else ""
    params = {"norad_id": norad_id}
    if epoch is not None:
        params["epoch"] = _utc(epoch)
    with engine.connect() as connection:
        row = connection.execute(
            text(f"""
                SELECT norad_cat_id, epoch, mean_motion, eccentricity,
                       inclination, ra_of_asc_node, arg_of_pericenter,
                       mean_anomaly, bstar, mean_motion_dot,
                       COALESCE(mean_motion_ddot, 0.0) AS mean_motion_ddot,
                       COALESCE(element_set_no, 0) AS element_set_no,
                       COALESCE(rev_at_epoch, 0) AS rev_at_epoch
                FROM gp_history
                WHERE norad_cat_id = :norad_id {where_epoch}
                ORDER BY epoch DESC
                LIMIT 1
            """),
            params,
        ).mappings().first()
    if row is None:
        raise LookupError(f"No GP history found for NORAD {norad_id}")
    return satrec_from_gp(dict(row))


def propagate(norad_id: int, times: Iterable[datetime]) -> list[dict]:
    satellite = satrec_from_database(norad_id)
    return propagate_with_satrec(satellite, norad_id, times)


def propagate_with_satrec(
    satellite: Satrec,
    norad_id: int,
    times: Iterable[datetime],
) -> list[dict]:
    results = []
    for timestamp in times:
        timestamp = _utc(timestamp)
        jd, fr = jday(
            timestamp.year,
            timestamp.month,
            timestamp.day,
            timestamp.hour,
            timestamp.minute,
            timestamp.second + timestamp.microsecond / 1_000_000,
        )
        error, position, velocity = satellite.sgp4(jd, fr)
        if error:
            raise ValueError(f"SGP4 error code {error} for NORAD {norad_id}")
        results.append(
            {
                "norad_id": norad_id,
                "timestamp": timestamp,
                "frame": "TEME",
                "position": {
                    "x": float(position[0]),
                    "y": float(position[1]),
                    "z": float(position[2]),
                },
                "velocity": {
                    "x": float(velocity[0]),
                    "y": float(velocity[1]),
                    "z": float(velocity[2]),
                },
            }
        )
    return results


def _satellite_for_skyfield(satrec: Satrec) -> EarthSatellite:
    line1, line2 = export_tle(satrec)
    return EarthSatellite(line1, line2)


def ground_track(
    norad_id: int,
    start: datetime,
    end: datetime,
    step: timedelta,
) -> list[dict]:
    start = _utc(start)
    end = _utc(end)
    if step.total_seconds() <= 0:
        raise ValueError("step must be positive")

    satrec = satrec_from_database(norad_id)
    satellite = _satellite_for_skyfield(satrec)
    timescale = load.timescale()
    timestamps = []
    current = start
    while current <= end:
        timestamps.append(current)
        current += step

    sky_times = timescale.from_datetimes(timestamps)
    subpoints = wgs84.subpoint(satellite.at(sky_times))
    latitudes = subpoints.latitude.degrees
    longitudes = subpoints.longitude.degrees
    altitudes_km = subpoints.elevation.km

    track = []
    for timestamp, latitude, longitude, altitude in zip(
        timestamps, latitudes, longitudes, altitudes_km
    ):
        track.append(
            {
                "timestamp": timestamp,
                "latitude": float(latitude),
                "longitude": float(longitude),
                "altitude_km": float(altitude),
            }
        )
    return track


def derived_values(satrec: Satrec) -> dict:
    mean_motion_rad_s = satrec.no_kozai
    period_seconds = 2 * 3.141592653589793 / mean_motion_rad_s
    speed = sqrt(satrec.no_kozai * satrec.no_kozai * EARTH_MU_KM3_S2 / 2)
    return {
        "orbital_period_seconds": float(period_seconds),
        "speed_kms_approx": float(speed),
    }

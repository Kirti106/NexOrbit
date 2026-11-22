from datetime import datetime, timezone

from sgp4.api import Satrec, WGS72, jday


def propagate_tle(line1: str, line2: str, when: datetime):
    if when.tzinfo is None:
        when = when.replace(tzinfo=timezone.utc)
    when = when.astimezone(timezone.utc)

    satellite = Satrec.twoline2rv(line1, line2)
    jd, fr = jday(
        when.year, when.month, when.day,
        when.hour, when.minute,
        when.second + when.microsecond / 1_000_000,
    )
    error, position, velocity = satellite.sgp4(jd, fr)

    if error != 0:
        raise ValueError(f"SGP4 propagation failed with error code {error}")

    return {
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


def propagate_gp(elements, when: datetime):
    if when.tzinfo is None:
        when = when.replace(tzinfo=timezone.utc)
    when = when.astimezone(timezone.utc)
    if not elements.mean_motion or elements.mean_motion <= 0:
        raise ValueError("GP mean motion is missing or invalid")
    epoch = elements.epoch
    if epoch.tzinfo is None:
        epoch = epoch.replace(tzinfo=timezone.utc)
    epoch_jd, epoch_fraction = jday(
        epoch.year,
        epoch.month,
        epoch.day,
        epoch.hour,
        epoch.minute,
        epoch.second + epoch.microsecond / 1_000_000,
    )
    satellite = Satrec()
    satellite.sgp4init(
        WGS72,
        "i",
        elements.norad_cat_id,
        epoch_jd + epoch_fraction - 2433281.5,
        elements.bstar or 0.0,
        (elements.mean_motion_dot or 0.0) * 2 * 3.141592653589793 / 1440**2,
        (elements.mean_motion_ddot or 0.0) * 2 * 3.141592653589793 / 1440**3,
        elements.eccentricity or 0.0,
        (elements.arg_of_pericenter or 0.0) * 3.141592653589793 / 180,
        (elements.inclination or 0.0) * 3.141592653589793 / 180,
        (elements.mean_anomaly or 0.0) * 3.141592653589793 / 180,
        elements.mean_motion * 2 * 3.141592653589793 / 1440,
        (elements.ra_of_asc_node or 0.0) * 3.141592653589793 / 180,
    )
    jd, fraction = jday(
        when.year,
        when.month,
        when.day,
        when.hour,
        when.minute,
        when.second + when.microsecond / 1_000_000,
    )
    error, position, velocity = satellite.sgp4(jd, fraction)
    if error:
        raise ValueError(f"SGP4 propagation failed with error code {error}")
    return {
        "position": {axis: float(position[i]) for i, axis in enumerate(("x", "y", "z"))},
        "velocity": {axis: float(velocity[i]) for i, axis in enumerate(("x", "y", "z"))},
    }

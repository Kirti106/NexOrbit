from datetime import datetime, timezone
from sgp4.api import Satrec, jday


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

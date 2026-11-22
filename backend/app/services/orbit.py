from datetime import datetime, timezone

from sgp4.api import Satrec, jday


def propagate_tle(
    line1: str, line2: str, when: datetime
) -> dict[str, dict[str, float]]:
    timestamp = (
        when.replace(tzinfo=timezone.utc)
        if when.tzinfo is None
        else when.astimezone(timezone.utc)
    )
    satellite = Satrec.twoline2rv(line1, line2)
    jd, fraction = jday(
        timestamp.year,
        timestamp.month,
        timestamp.day,
        timestamp.hour,
        timestamp.minute,
        timestamp.second + timestamp.microsecond / 1_000_000,
    )
    error, position, velocity = satellite.sgp4(jd, fraction)
    if error:
        raise ValueError(f"SGP4 propagation failed with error code {error}")
    return {
        "position": dict(zip(("x", "y", "z"), map(float, position))),
        "velocity": dict(zip(("x", "y", "z"), map(float, velocity))),
    }

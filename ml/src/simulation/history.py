from __future__ import annotations

import pandas as pd


def altitude_band(perigee_km: float, apogee_km: float) -> str:
    altitude = (perigee_km + apogee_km) / 2
    if altitude < 2000:
        return "LEO"
    if altitude < 35786:
        return "MEO"
    if altitude < 43000:
        return "GEO"
    return "HEO"


def build_monthly_history(satcat: pd.DataFrame) -> pd.DataFrame:
    frame = satcat.copy()
    frame["launch_date"] = pd.to_datetime(frame["launch_date"], utc=True, errors="coerce")
    frame["decay_date"] = pd.to_datetime(frame["decay_date"], utc=True, errors="coerce")
    frame["object_type"] = frame["object_type"].fillna("UNKNOWN").astype(str).str.upper()
    frame["altitude_band"] = frame.apply(
        lambda row: altitude_band(
            float(row.get("perigee_km", 0) or 0),
            float(row.get("apogee_km", 0) or 0),
        ),
        axis=1,
    )

    launched = (
        frame.dropna(subset=["launch_date"])
        .assign(month=lambda value: pd.to_datetime(
            value["launch_date"].dt.strftime("%Y-%m") + "-01",
            utc=True,
        ))
        .groupby(["month", "object_type", "altitude_band"])
        .size()
        .rename("launches")
        .reset_index()
    )
    decayed = (
        frame.dropna(subset=["decay_date"])
        .assign(month=lambda value: pd.to_datetime(
            value["decay_date"].dt.strftime("%Y-%m") + "-01",
            utc=True,
        ))
        .groupby(["month", "object_type", "altitude_band"])
        .size()
        .rename("decays")
        .reset_index()
    )
    history = launched.merge(
        decayed,
        on=["month", "object_type", "altitude_band"],
        how="outer",
    ).fillna({"launches": 0, "decays": 0})
    history["month"] = pd.to_datetime(history["month"], utc=True)
    history = history.sort_values("month")
    history["in_orbit"] = (
        history.groupby(["object_type", "altitude_band"])["launches"].cumsum()
        - history.groupby(["object_type", "altitude_band"])["decays"].cumsum()
    )
    history["in_orbit"] = history["in_orbit"].clip(lower=0)
    return history

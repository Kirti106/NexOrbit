from __future__ import annotations

import pandas as pd


ALTITUDE_DECAY_RATES = {
    "LEO": 0.08,
    "MEO": 0.02,
    "GEO": 0.005,
    "HEO": 0.015,
}


def simulate(
    history: pd.DataFrame,
    *,
    horizon_months: int,
    launch_rate_multiplier: float = 1.0,
    disposal_compliance: float = 0.0,
    decay_rate_by_altitude: dict[str, float] | None = None,
) -> pd.DataFrame:
    if launch_rate_multiplier < 0:
        raise ValueError("launch_rate_multiplier must be non-negative")
    if not 0 <= disposal_compliance <= 1:
        raise ValueError("disposal_compliance must be between 0 and 1")

    decay_rates = dict(ALTITUDE_DECAY_RATES)
    if decay_rate_by_altitude:
        decay_rates.update(decay_rate_by_altitude)

    latest = (
        history.sort_values("month")
        .groupby(["object_type", "altitude_band"], as_index=False)
        .tail(1)
        .copy()
    )
    population = {
        (row.object_type, row.altitude_band): float(row.in_orbit)
        for row in latest.itertuples()
    }
    monthly_launches = (
        history.groupby(["object_type", "altitude_band"])["launches"]
        .mean()
        .to_dict()
    )

    if history.empty:
        month_start = pd.Timestamp.now(tz="UTC").to_period("M").to_timestamp()
    else:
        month_start = pd.Timestamp(history["month"].max()).to_period("M").to_timestamp()

    rows = []
    for horizon in range(1, horizon_months + 1):
        month = month_start + pd.DateOffset(months=horizon)
        for key in list(population):
            object_type, band = key
            launches = monthly_launches.get(key, 0.0) * launch_rate_multiplier
            if object_type == "DEBRIS":
                debris_reduction = launches * disposal_compliance
                launches -= debris_reduction
            decay = population[key] * decay_rates.get(band, 0.01)
            population[key] = max(0.0, population[key] + launches - decay)
        rows.append(
            {
                "month": month,
                "projected_objects": round(sum(population.values())),
                "projected_payloads": round(sum(
                    count for (kind, _), count in population.items()
                    if kind == "PAYLOAD"
                )),
                "projected_debris": round(sum(
                    count for (kind, _), count in population.items()
                    if kind == "DEBRIS"
                )),
            }
        )
    return pd.DataFrame(rows)

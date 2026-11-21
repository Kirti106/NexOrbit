from __future__ import annotations

import numpy as np
import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing


def forecast_in_orbit(
    monthly_history: pd.DataFrame,
    horizon_months: int = 24,
    confidence_level: float = 0.95,
) -> pd.DataFrame:
    frame = monthly_history.sort_values("month").copy()
    totals = (
        frame.groupby("month")["in_orbit"]
        .sum()
        .asfreq("MS")
        .ffill()
    )
    if len(totals) < 4:
        last = float(totals.iloc[-1]) if len(totals) else 0.0
        future = pd.date_range(
            start=totals.index[-1] + pd.offsets.MonthBegin()
            if len(totals)
            else pd.Timestamp.now(tz="UTC"),
            periods=horizon_months,
            freq="MS",
        )
        forecast = pd.DataFrame(
            {
                "month": future,
                "forecast": last,
                "lower": max(0.0, last * (1 - (1 - confidence_level))),
                "upper": last,
            }
        )
        return forecast

    trend = "add" if totals.iloc[-1] >= totals.iloc[0] else "add"
    model = ExponentialSmoothing(
        totals,
        trend=trend,
        seasonal=None,
        initialization_method="estimated",
    ).fit(optimized=True)
    predicted = model.forecast(horizon_months)
    residual_std = float(np.std(model.resid, ddof=1)) if len(model.resid) > 1 else 0.0
    z = 1.96 if confidence_level == 0.95 else 1.64
    lower = np.maximum(0, predicted.to_numpy() - z * residual_std)
    upper = predicted.to_numpy() + z * residual_std
    return pd.DataFrame(
        {
            "month": predicted.index,
            "forecast": predicted.to_numpy(),
            "lower": lower,
            "upper": upper,
        }
    )

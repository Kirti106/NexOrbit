"""Anomaly detection for anomalous orbital element changes.

This module detects anomalous element changes only. Its scores do not confirm
satellite maneuvers, drag changes, or bad source data.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest


FEATURES = [
    "mean_motion_delta",
    "eccentricity_delta",
    "inclination_delta",
    "raan_delta",
    "arg_pericenter_delta",
    "bstar_delta",
    "time_gap_seconds",
]


def build_anomaly_features(history: pd.DataFrame) -> pd.DataFrame:
    frame = history.sort_values(["norad_cat_id", "epoch"]).copy()
    frame["epoch"] = pd.to_datetime(frame["epoch"], utc=True)
    frame["time_gap_seconds"] = (
        frame.groupby("norad_cat_id")["epoch"].diff().dt.total_seconds()
    )
    for source, target in [
        ("mean_motion", "mean_motion_delta"),
        ("eccentricity", "eccentricity_delta"),
        ("inclination", "inclination_delta"),
        ("ra_of_asc_node", "raan_delta"),
        ("arg_pericenter", "arg_pericenter_delta"),
        ("bstar", "bstar_delta"),
    ]:
        frame[target] = frame.groupby("norad_cat_id")[source].diff()
    return frame.dropna(subset=FEATURES).copy()


def robust_z_scores(frame: pd.DataFrame) -> pd.Series:
    scores = pd.Series(0.0, index=frame.index)
    for _, group in frame.groupby("norad_cat_id"):
        scale = 1.4826
        for feature in FEATURES:
            values = group[feature].astype(float)
            median = values.median()
            mad = (values - median).abs().median()
            denominator = scale * mad
            if denominator > 0:
                scores.loc[group.index] += np.abs(
                    (values - median) / denominator
                )
    return scores


def isolation_forest_scores(frame: pd.DataFrame, contamination: float = 0.05) -> np.ndarray:
    model = IsolationForest(
        contamination=contamination,
        random_state=42,
        n_estimators=200,
    )
    matrix = frame[FEATURES].fillna(0).replace([np.inf, -np.inf], 0).to_numpy()
    model.fit(matrix)
    return -model.score_samples(matrix)


def detect(frame: pd.DataFrame, robust_z_threshold: float = 6.0) -> pd.DataFrame:
    features = build_anomaly_features(frame)
    if features.empty:
        return pd.DataFrame(columns=[*frame.columns, "score", "flag", "top_feature"])

    robust = robust_z_scores(features)
    isolation = isolation_forest_scores(features)
    features["score"] = (robust.astype(float).to_numpy() + isolation) / 2
    features["flag"] = features["score"] >= robust_z_threshold
    features["top_feature"] = features[FEATURES].abs().idxmax(axis=1)
    return features

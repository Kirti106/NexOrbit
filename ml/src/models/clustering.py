"""Orbital shell clustering and object-type classification."""

from __future__ import annotations

import pandas as pd
from sklearn.cluster import DBSCAN, KMeans
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split

FEATURES = [
    "altitude_km",
    "perigee_km",
    "apogee_km",
    "inclination",
    "eccentricity",
    "period_minutes",
]


def kmeans_clusters(frame: pd.DataFrame, clusters: int = 6) -> pd.DataFrame:
    result = frame.copy()
    matrix = result[FEATURES].fillna(0)
    scaled = StandardScaler().fit_transform(matrix)
    result["cluster"] = KMeans(
        n_clusters=min(clusters, len(result)),
        random_state=42,
        n_init=10,
    ).fit_predict(scaled)
    return result


def dbscan_clusters(
    frame: pd.DataFrame,
    eps: float = 0.8,
    min_samples: int = 5,
) -> pd.DataFrame:
    result = frame.copy()
    scaled = StandardScaler().fit_transform(result[FEATURES].fillna(0))
    result["cluster"] = DBSCAN(eps=eps, min_samples=min_samples).fit_predict(scaled)
    return result


def classify_object_type(frame: pd.DataFrame) -> dict:
    known = frame[
        frame["object_type"].notna()
        & frame["object_type"].str.upper().isin(
            ["PAYLOAD", "DEBRIS", "ROCKET BODY"]
        )
    ].copy()
    if known["object_type"].nunique() < 2 or len(known) < 4:
        return {"error": "Not enough known object types"}

    known = known.sort_values("launch_date") if "launch_date" in known else known
    split = int(len(known) * 0.8)
    train = known.iloc[:split]
    test = known.iloc[split:]
    if test.empty:
        return {"error": "Time split is empty"}

    preprocess = ColumnTransformer(
        [("numeric", StandardScaler(), FEATURES)],
    )
    pipeline = Pipeline(
        [
            ("preprocess", preprocess),
            ("model", RandomForestClassifier(
                class_weight="balanced",
                n_estimators=300,
                random_state=42,
            )),
        ]
    )
    pipeline.fit(train[FEATURES], train["object_type"].str.upper())
    predictions = pipeline.predict(test[FEATURES])
    return classification_report(
        test["object_type"].str.upper(),
        predictions,
        output_dict=True,
        zero_division=0,
    )

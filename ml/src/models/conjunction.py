"""SOCRATES-derived conjunction risk tiers.

Labels and rankings describe risk tiers derived from SOCRATES snapshots.
They are not actual collision probabilities or confirmed collision forecasts.

MAX_PROB is used only to derive labels and is never included as a model feature.
"""

from __future__ import annotations

from datetime import datetime

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, average_precision_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.model_selection import TimeSeriesSplit

FEATURES = [
    "min_range_km",
    "rel_speed_kms",
    "dse_1",
    "dse_2",
    "dilution",
    "time_to_tca_seconds",
    "object_type_1",
    "object_type_2",
]


def constellation_base(name: str | None) -> str:
    if not name:
        return ""
    first = str(name).upper().strip().split()[0]
    return "".join(character for character in first.split("-")[0] if character.isalpha())


def is_constellation_artifact(row: pd.Series, range_km: float = 1.0) -> bool:
    name1 = row.get("object_name_1")
    name2 = row.get("object_name_2")
    if name1 is None or name2 is None:
        name1 = row.get("OBJECT_NAME_1")
        name2 = row.get("OBJECT_NAME_2")
    return (
        float(row.get("min_range_km", row.get("TCA_RANGE", 999))) <= range_km
        and constellation_base(name1) != ""
        and constellation_base(name1) == constellation_base(name2)
    )


def derive_risk_tier(
    row: pd.Series,
    *,
    low_max_probability_exclusive: float = 1e-5,
    medium_max_probability_exclusive: float = 1e-3,
    high_min_range_km: float = 50.0,
) -> str:
    if is_constellation_artifact(row):
        return "low"
    probability = row["max_prob"]
    if pd.isna(probability):
        return "low"
    if probability >= medium_max_probability_exclusive or (
        probability >= low_max_probability_exclusive
        and row["min_range_km"] <= high_min_range_km
    ):
        return "high"
    if probability >= low_max_probability_exclusive:
        return "medium"
    return "low"


def prepare_events(events: pd.DataFrame) -> pd.DataFrame:
    frame = events.copy()
    frame["tca"] = pd.to_datetime(frame["tca"], utc=True)
    frame["fetched_at"] = pd.to_datetime(frame["fetched_at"], utc=True)
    frame["time_to_tca_seconds"] = (
        frame["tca"] - frame["fetched_at"]
    ).dt.total_seconds()
    frame["object_type_1"] = frame.get("object_type_1", "UNKNOWN").fillna("UNKNOWN")
    frame["object_type_2"] = frame.get("object_type_2", "UNKNOWN").fillna("UNKNOWN")
    frame["is_constellation_artifact"] = frame.apply(
        is_constellation_artifact,
        axis=1,
    )
    frame["risk_weight"] = frame["is_constellation_artifact"].map(
        {True: 0.1, False: 1.0}
    )
    frame["risk_tier"] = frame.apply(derive_risk_tier, axis=1)
    return frame


def time_split(frame: pd.DataFrame):
    frame = frame.sort_values("fetched_at").reset_index(drop=True)
    split = int(len(frame) * 0.8)
    return frame.iloc[:split], frame.iloc[split:]


def build_pipeline(model) -> Pipeline:
    numeric = [name for name in FEATURES if name not in {"object_type_1", "object_type_2"}]
    categorical = ["object_type_1", "object_type_2"]
    preprocess = ColumnTransformer(
        [
            ("numeric", StandardScaler(), numeric),
            ("categorical", OneHotEncoder(handle_unknown="ignore"), categorical),
        ]
    )
    return Pipeline([("preprocess", preprocess), ("model", model)])


def train_and_evaluate(frame: pd.DataFrame) -> dict:
    frame = prepare_events(frame)
    train, test = time_split(frame)
    if len(train) < 2 or len(test) < 1:
        return {"error": "Not enough chronological SOCRATES samples"}
    if train["risk_tier"].nunique() < 2:
        return {"error": "Training split contains fewer than two risk tiers"}

    models = {
        "logistic_regression": LogisticRegression(
            class_weight="balanced", max_iter=1000, random_state=42
        ),
        "random_forest": RandomForestClassifier(
            class_weight="balanced", n_estimators=300, random_state=42
        ),
        "gradient_boosting": GradientBoostingClassifier(random_state=42),
    }
    results = {}
    for name, model in models.items():
        pipeline = build_pipeline(model)
        pipeline.fit(train[FEATURES], train["risk_tier"])
        prediction = pipeline.predict(test[FEATURES])
        report = classification_report(
            test["risk_tier"],
            prediction,
            output_dict=True,
            zero_division=0,
        )
        if hasattr(pipeline, "predict_proba"):
            probabilities = pipeline.predict_proba(test[FEATURES])
            classes = pipeline.classes_
            pr_auc = {}
            for index, risk_tier in enumerate(classes):
                binary = (test["risk_tier"] == risk_tier).astype(int)
                pr_auc[risk_tier] = float(
                    average_precision_score(binary, probabilities[:, index])
                )
            report["pr_auc_per_class"] = pr_auc
        results[name] = report
    return results


def rank_events(events: pd.DataFrame) -> pd.DataFrame:
    frame = prepare_events(events)
    tier_rank = {"high": 3, "medium": 2, "low": 1}
    frame["_tier_rank"] = frame["risk_tier"].map(tier_rank)
    frame["_probability"] = frame["max_prob"].fillna(0)
    frame["_effective_score"] = (
        frame["_probability"] * frame["risk_weight"]
    )
    return frame.sort_values(
        ["_tier_rank", "_effective_score", "min_range_km"],
        ascending=[False, False, True],
    ).drop(columns=["_tier_rank", "_probability", "_effective_score"])

import pandas as pd

try:
    from ml.src.models.anomaly import build_anomaly_features, detect
    from ml.src.models.conjunction import derive_risk_tier, rank_events
    from ml.src.simulation.history import build_monthly_history, altitude_band
except ModuleNotFoundError:
    from src.models.anomaly import build_anomaly_features, detect
    from src.models.conjunction import derive_risk_tier, rank_events
    from src.simulation.history import build_monthly_history, altitude_band


def test_risk_tier_probability_is_not_a_feature():
    low = pd.Series({"max_prob": 1e-8, "min_range_km": 100})
    high = pd.Series({"max_prob": 1e-2, "min_range_km": 20})
    assert derive_risk_tier(low) == "low"
    assert derive_risk_tier(high) == "high"


def test_constellation_artifact_is_downweighted():
    artifact = pd.Series({
        "max_prob": 1.0,
        "min_range_km": 0.018,
        "object_name_1": "STARLINK-1296 [P]",
        "object_name_2": "STARLINK-2576 [+]",
    })
    assert derive_risk_tier(artifact) == "low"


def test_anomaly_features_and_flags():
    frame = pd.DataFrame(
        [
            {"norad_cat_id": 1, "epoch": "2026-01-01T00:00:00Z", "mean_motion": 15, "eccentricity": 0.001, "inclination": 51, "ra_of_asc_node": 10, "arg_pericenter": 20, "bstar": 1e-5},
            {"norad_cat_id": 1, "epoch": "2026-01-02T00:00:00Z", "mean_motion": 15.2, "eccentricity": 0.002, "inclination": 52, "ra_of_asc_node": 11, "arg_pericenter": 21, "bstar": 2e-5},
        ]
    )
    result = build_anomaly_features(frame)
    assert "time_gap_seconds" in result
    assert len(result) == 1


def test_altitude_bands_and_monthly_history():
    assert altitude_band(400, 500) == "LEO"
    frame = pd.DataFrame(
        [
            {"launch_date": "2026-01-01T00:00:00Z", "decay_date": None, "object_type": "PAYLOAD", "perigee_km": 400, "apogee_km": 500},
            {"launch_date": "2026-02-01T00:00:00Z", "decay_date": "2026-03-01T00:00:00Z", "object_type": "DEBRIS", "perigee_km": 600, "apogee_km": 700},
        ]
    )
    history = build_monthly_history(frame)
    assert not history.empty

from datetime import datetime, timezone
import math
from types import SimpleNamespace

import httpx
import pytest

from app.config import Settings
from app.services.ml_client import MLClient
from app.services.orbit import propagate_gp, propagate_tle
from app.services.risk import risk_tier


def test_risk_tier_classification_edges():
    assert risk_tier(1e-3, 500, False) == "high"
    assert risk_tier(1e-5, 50, False) == "high"
    assert risk_tier(1e-5, 50.1, False) == "medium"
    assert risk_tier(1.0, 0.1, True) == "low"
    assert risk_tier(None, None, False) == "low"


def test_sgp4_propagation_returns_finite_teme_vectors():
    line1 = "1 25544U 98067A   21275.51005787  .00001490  00000-0  33278-4 0  9993"
    line2 = "2 25544  51.6442 209.8189 0003886  42.3161  77.7092 15.48815327305135"
    result = propagate_tle(line1, line2, datetime(2021, 10, 2, 12, 14, 29, tzinfo=timezone.utc))
    assert set(result["position"]) == {"x", "y", "z"}
    assert all(math.isfinite(value) for vector in result.values() for value in vector.values())


def test_sgp4_propagates_stored_gp_elements():
    elements = SimpleNamespace(
        norad_cat_id=25544,
        epoch=datetime(2021, 10, 2, 12, 14, 29, tzinfo=timezone.utc),
        mean_motion=15.48815327,
        mean_motion_dot=0.0000149,
        mean_motion_ddot=0.0,
        eccentricity=0.0003886,
        arg_of_pericenter=42.3161,
        inclination=51.6442,
        mean_anomaly=77.7092,
        ra_of_asc_node=209.8189,
        bstar=0.000033278,
    )
    result = propagate_gp(elements, elements.epoch)
    assert all(math.isfinite(value) for vector in result.values() for value in vector.values())


@pytest.mark.asyncio
async def test_ml_client_retries_a_server_error():
    calls = 0

    def handler(request):
        nonlocal calls
        calls += 1
        if calls == 1:
            return httpx.Response(503, request=request)
        return httpx.Response(200, json={"status": "ok"}, request=request)

    async with httpx.AsyncClient(
        base_url="http://ml.test", transport=httpx.MockTransport(handler)
    ) as client:
        result = await MLClient(Settings(ml_api_url="http://ml.test"), client).get("/health")
    assert result == {"status": "ok"}
    assert calls == 2

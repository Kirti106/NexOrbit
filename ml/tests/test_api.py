from datetime import datetime, timezone
import math

from fastapi.testclient import TestClient
from skyfield.api import load as skyfield_load

try:
    from ml.src.api.app import app
    from ml.src.propagation.sgp4 import _satellite_for_skyfield, satrec_from_database
except ModuleNotFoundError:
    from src.api.app import app
    from src.propagation.sgp4 import _satellite_for_skyfield, satrec_from_database


client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] in {"healthy", "degraded"}
    assert body["model_version"]
    assert body["generated_at"]


def test_satellites_endpoint():
    response = client.get("/satellites", params={"limit": 10})
    assert response.status_code == 200
    body = response.json()
    assert body["total"] > 0
    assert len(body["items"]) <= 10


def test_satellites_live_endpoint():
    response = client.get("/satellites/live", params={"limit": 20})
    assert response.status_code == 200
    body = response.json()
    assert len(body["items"]) <= 20
    assert body["frame"] == "TEME position converted to geodetic"


def test_position_endpoint():
    response = client.get("/satellites/25544/position")
    assert response.status_code in {200, 404}
    if response.status_code == 200:
        body = response.json()
        assert body["norad_id"] == 25544
        assert body["frame"] == "TEME"
        assert "position" in body


def test_ground_track_endpoint():
    response = client.get("/satellites/25544/ground-track", params={"hours": 1, "step_s": 60})
    assert response.status_code in {200, 404}
    if response.status_code == 200:
        assert len(response.json()["points"]) == 61


def test_conjunctions_endpoint():
    response = client.get("/conjunctions", params={"limit": 10, "include_artifacts": "false"})
    assert response.status_code == 200
    body = response.json()
    assert body["basis"] == "SOCRATES-derived, predicted, not observed"
    assert len(body["items"]) <= 10
    assert all(not item["is_artifact"] for item in body["items"])


def test_stats_endpoint():
    response = client.get("/stats")
    assert response.status_code == 200
    body = response.json()
    assert body["tracked_satellites"] > 0
    assert body["conjunctions"] > 0


def test_anomalies_endpoint():
    response = client.get("/anomalies", params={"limit": 10})
    assert response.status_code == 200
    body = response.json()
    assert len(body["items"]) <= 10
    assert body["basis"] == "cross-sectional element profile, not maneuver detection"


def test_iss_sgp4_matches_skyfield():
    satrec = satrec_from_database(25544)
    sky_satellite = _satellite_for_skyfield(satrec)
    timestamp = datetime.now(timezone.utc)
    from sgp4.api import jday

    jd, fr = jday(timestamp.year, timestamp.month, timestamp.day,
                   timestamp.hour, timestamp.minute,
                   timestamp.second + timestamp.microsecond / 1_000_000)
    error, module_position, _ = satrec.sgp4(jd, fr)
    assert error == 0
    sky_time = skyfield_load.timescale().from_datetime(timestamp)
    sky_position = sky_satellite.at(sky_time).position.km
    difference_km = math.sqrt(sum(
        (float(module_position[i]) - float(sky_position[i])) ** 2
        for i in range(3)
    ))
    # TEME and Skyfield GCRS axes differ slightly; 50 km is the stated
    # cross-frame acceptance tolerance for this ISS smoke check.
    assert difference_km < 50.0

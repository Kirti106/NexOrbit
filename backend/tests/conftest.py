import os

from datetime import datetime, timedelta, timezone

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


def pytest_configure():
    test_database_url = os.getenv("TEST_DATABASE_URL")
    if test_database_url:
        os.environ["DATABASE_URL"] = test_database_url


@pytest.fixture
def api():
    from app.config import Settings
    from app.db.base import Base
    from app.db.session import get_db
    from app.deps import ml_http_dependency
    from app.main import create_app
    from app.models.satellite import Conjunction, GPHistory, Satellite
    from app.routers.v1.analytics import ml_client as analytics_ml_client
    from app.routers.v1.satellites import ml_client as satellites_ml_client
    from app.services.ml_client import MLClient

    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(test_engine)
    test_sessions = sessionmaker(bind=test_engine, autoflush=False)
    settings = Settings(
        database_url="sqlite://",
        ml_api_url="http://ml.test",
        admin_api_key="test-admin-key",
        scheduler_enabled=False,
    )
    application = create_app(settings)
    now = datetime.now(timezone.utc)
    with test_sessions() as db:
        db.add(
            Satellite(
                norad_cat_id=25544,
                object_name="ISS (ZARYA)",
                object_type="PAYLOAD",
                owner_country="US",
                status="operational",
                updated_at=now,
            )
        )
        db.add(
            GPHistory(
                norad_cat_id=25544,
                epoch=now - timedelta(minutes=5),
                mean_motion=15.5,
                eccentricity=0.001,
                inclination=51.6,
                fetched_at=now,
            )
        )
        db.add(
            Conjunction(
                norad_cat_id_1=25544,
                norad_cat_id_2=48291,
                object_name_1="ISS (ZARYA)",
                object_name_2="OBJECT 48291",
                tca=now + timedelta(days=1),
                min_range_km=8.0,
                rel_speed_kms=10.2,
                max_prob=1e-4,
                is_constellation_artifact=False,
                risk_tier="high",
                fetched_at=now,
            )
        )
        db.commit()

    def override_db():
        with test_sessions() as db:
            yield db

    mock_transport = httpx.MockTransport(_ml_handler)
    mock_http = httpx.AsyncClient(base_url="http://ml.test", transport=mock_transport)
    application.dependency_overrides[get_db] = override_db
    application.dependency_overrides[satellites_ml_client] = lambda: MLClient(
        settings, mock_http
    )
    application.dependency_overrides[analytics_ml_client] = lambda: MLClient(
        settings, mock_http
    )
    application.dependency_overrides[ml_http_dependency] = lambda: mock_http
    with TestClient(application) as test_client:
        yield test_client
    import asyncio

    asyncio.run(mock_http.aclose())
    Base.metadata.drop_all(test_engine)
    test_engine.dispose()


def _ml_handler(request: httpx.Request) -> httpx.Response:
    if request.url.path == "/health":
        return httpx.Response(200, json={"status": "healthy"})
    if request.url.path == "/satellites/live":
        return httpx.Response(
            200,
            json={
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "frame": "TEME position converted to geodetic",
                "items": [
                    {
                        "norad_id": 25544,
                        "name": "ISS (ZARYA)",
                        "latitude": 10.0,
                        "longitude": -20.0,
                        "altitude_km": 420.0,
                    }
                ],
            },
        )
    if request.url.path.endswith("/position"):
        return httpx.Response(
            200,
            json={
                "norad_id": 25544,
                "name": "ISS (ZARYA)",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "frame": "TEME",
                "position": {"x": 1.0, "y": 2.0, "z": 3.0},
                "velocity": {"x": 4.0, "y": 5.0, "z": 6.0},
                "altitude_km": 420.0,
                "speed_kms": 8.77,
            },
        )
    if request.url.path.endswith("/ground-track"):
        return httpx.Response(
            200,
            json={
                "norad_id": 25544,
                "points": [
                    {
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "latitude": 10.0,
                        "longitude": -20.0,
                        "altitude_km": 420.0,
                    }
                ],
            },
        )
    if request.url.path == "/anomalies":
        return httpx.Response(
            200,
            json={
                "basis": "cross-sectional element profile, not maneuver detection",
                "items": [],
            },
        )
    return httpx.Response(404, json={"detail": "not found"})

from datetime import datetime, timezone
from types import SimpleNamespace

from app.routers.v1 import admin
from app.routers.v1 import system
from app.repositories import catalog
from app.core.cache import cache
from app.core.rate_limit import InMemoryRateLimiter


def test_satellite_catalog_endpoints(api):
    response = api.get("/api/v1/satellites", params={"q": "25544"})
    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["orbit_class"] == "LEO"
    assert api.get("/api/v1/satellites/25544").json()["name"] == "ISS (ZARYA)"
    assert api.get("/api/v1/satellites/99999").status_code == 404


def test_ml_backed_orbit_endpoints(api):
    now = datetime.now(timezone.utc).isoformat()
    assert api.get("/api/v1/satellites/live").json()["items"][0]["norad_id"] == 25544
    position = api.get(
        "/api/v1/satellites/25544/position", params={"time": now}
    )
    assert position.status_code == 200
    assert position.json()["position"]["x"] == 1.0
    assert position.json()["degraded"] is False
    track = api.get("/api/v1/satellites/25544/ground-track")
    assert track.status_code == 200
    assert len(track.json()["points"]) == 1
    assert api.get("/api/v1/anomalies").json()["basis"] == (
        "unusual orbit profile, not maneuver detection"
    )


def test_conjunction_analytics_and_health_endpoints(api):
    conjunctions = api.get(
        "/api/v1/conjunctions", params={"risk_tier": "high"}
    ).json()
    assert conjunctions["total"] == 1
    assert conjunctions["basis"] == "predicted, not observed"
    assert api.get(
        f"/api/v1/conjunctions/{conjunctions['items'][0]['id']}"
    ).json()["risk_tier"] == "high"
    assert api.get("/api/v1/conjunctions/999").status_code == 404
    stats = api.get("/api/v1/stats")
    assert stats.status_code == 200 and stats.json()["total_objects"] == 1
    analytics = api.get("/api/v1/analytics", params={"period": "7D"})
    assert analytics.status_code == 200
    assert analytics.json()["conjunctions_per_day"]
    assert api.get("/api/v1/health").json()["status"] == "healthy"
    assert api.get("/api/v1/ready").json() == {"status": "ready"}
    alerts = api.get("/api/v1/alerts", params={"limit": 3})
    assert alerts.status_code == 200
    assert alerts.json()["total"] == 1


def test_satellite_history_and_conjunction_routes_use_repository(api, monkeypatch):
    now = datetime.now(timezone.utc)

    def fake_satellite(_db, norad_id):
        return (object(), None) if norad_id == 25544 else (None, None)

    monkeypatch.setattr(catalog, "get_satellite", fake_satellite)
    monkeypatch.setattr(
        catalog,
        "list_gp_history",
        lambda _db, _norad_id, limit: [
            SimpleNamespace(
                epoch=now,
                mean_motion=15.5,
                eccentricity=0.001,
                inclination=51.6,
                bstar=0.0001,
            )
        ][:limit],
    )
    row = SimpleNamespace(
        id=1,
        norad_cat_id_1=25544,
        norad_cat_id_2=48291,
        object_name_1="ISS (ZARYA)",
        object_name_2="OBJECT 48291",
        tca=now,
        min_range_km=8.0,
        rel_speed_kms=10.2,
        max_prob=1e-4,
        is_constellation_artifact=False,
        fetched_at=now,
    )
    monkeypatch.setattr(catalog, "list_conjunctions", lambda *_args, **_kwargs: (1, [row]))

    history = api.get("/api/v1/satellites/25544/history", params={"limit": 1})
    assert history.status_code == 200
    assert history.json()["items"][0]["bstar"] == 0.0001
    assert api.get("/api/v1/satellites/99999/history").status_code == 404

    conjunctions = api.get("/api/v1/satellites/25544/conjunctions")
    assert conjunctions.status_code == 200
    assert conjunctions.json()["items"][0]["basis"] == "predicted, not observed"
    assert api.get("/api/v1/satellites/99999/conjunctions").status_code == 404


def test_conjunction_summary_and_meta_use_repository(api, monkeypatch):
    cache.clear()
    now = datetime.now(timezone.utc)
    counts = {
        "total": 1,
        "by_risk_tier": {"low": 0, "medium": 0, "high": 1},
        "by_severity": {
            "critical": 0,
            "high": 1,
            "medium": 0,
            "low": 0,
            "unknown": 0,
        },
    }
    monkeypatch.setattr(catalog, "conjunction_summary_counts", lambda *_args, **_kwargs: counts)
    monkeypatch.setattr(
        catalog,
        "meta_snapshot",
        lambda _db: {
            "gp_history_fetched_at": now,
            "conjunctions_fetched_at": now,
        },
    )

    summary = api.get("/api/v1/conjunctions/summary")
    assert summary.status_code == 200
    assert summary.json()["all"]["by_risk_tier"]["high"] == 1
    assert summary.json()["basis"] == "predicted, not observed"

    meta = api.get("/api/v1/meta")
    assert meta.status_code == 200
    assert meta.json()["api_version"] == "2.0.0"
    assert "not observed collisions" in meta.json()["data_basis"]["conjunctions"]


def test_cacheable_gets_return_etag_and_support_not_modified(api):
    cache.clear()
    paths = (
        "/api/v1/stats",
        "/api/v1/analytics",
        "/api/v1/meta",
        "/api/v1/conjunctions/summary",
    )
    for path in paths:
        first = api.get(path)
        assert first.status_code == 200
        etag = first.headers["etag"]
        assert first.headers["cache-control"].startswith("public, max-age=")
        second = api.get(path, headers={"If-None-Match": etag})
        assert second.status_code == 304
        assert second.headers["etag"] == etag


def test_conjunction_export_streams_filtered_csv_and_json(api):
    json_response = api.get(
        "/api/v1/conjunctions/export",
        params={"format": "json", "risk_tier": "high", "severity": "high"},
    )
    assert json_response.status_code == 200
    assert json_response.headers["content-type"].startswith("application/json")
    assert len(json_response.json()) == 1
    assert json_response.json()[0]["basis"] == "predicted, not observed"

    csv_response = api.get(
        "/api/v1/conjunctions/export",
        params={"format": "csv", "severity": "high"},
    )
    assert csv_response.status_code == 200
    assert csv_response.headers["content-type"].startswith("text/csv")
    assert "max_prob" in csv_response.text.splitlines()[0]
    assert len(csv_response.text.splitlines()) == 2
    assert api.get(
        "/api/v1/conjunctions/export", params={"limit": 5001}
    ).status_code == 422


def test_global_rate_limit_pagination_cap_and_security_headers(api):
    capped = api.get("/api/v1/satellites", params={"offset": 100001})
    assert capped.status_code == 422
    assert capped.json()["error"]["code"] == "pagination_limit_exceeded"

    gzip_response = api.get("/openapi.json", headers={"Accept-Encoding": "gzip"})
    assert gzip_response.status_code == 200
    assert gzip_response.headers.get("content-encoding") == "gzip"
    assert gzip_response.headers["x-content-type-options"] == "nosniff"
    assert gzip_response.headers["x-frame-options"] == "DENY"

    api.app.state.rate_limiter = InMemoryRateLimiter(2)
    assert api.get("/api/v1/health").status_code == 200
    assert api.get("/api/v1/health").status_code == 200
    limited = api.get("/api/v1/health")
    assert limited.status_code == 429
    assert limited.json()["error"]["code"] == "rate_limited"


def test_ready_fails_when_a_required_table_is_missing(api, monkeypatch):
    monkeypatch.setattr(
        system,
        "required_tables_available",
        lambda _db: {
            "satellites": True,
            "gp_history": False,
            "conjunctions": True,
        },
    )
    response = api.get("/api/v1/ready")
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "database_not_ready"


def test_admin_auth_rate_path_and_validation(api, monkeypatch):
    calls = []

    async def fake_sync_gp(db, group):
        calls.append(group)
        return {
            "source": "CelesTrak",
            "received": 1,
            "inserted_or_updated": 1,
            "message": "ok",
        }

    monkeypatch.setattr(admin, "sync_gp", fake_sync_gp)
    path = "/api/v1/admin/sync/gp"
    assert api.post(path).status_code == 401
    response = api.post(path, headers={"X-API-Key": "test-admin-key"})
    assert response.status_code == 200
    assert calls == ["active"]
    assert api.post(
        "/api/v1/admin/sync/conjunctions",
        headers={"X-API-Key": "test-admin-key"},
    ).status_code == 503
    assert api.get("/api/v1/analytics", params={"period": "2D"}).status_code == 422
    assert api.get("/api/v1/satellites", params={"orbit_class": "X"}).status_code == 422

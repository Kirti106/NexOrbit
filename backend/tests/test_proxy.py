"""Run from backend/: pip install pytest && pytest -q"""
import httpx
from fastapi.testclient import TestClient

from app.main import app
from app.services import ml_client

client = TestClient(app)


def _use_upstream(handler):
    ml_client._client = httpx.AsyncClient(
        base_url="http://ml.test", transport=httpx.MockTransport(handler)
    )


def test_conjunctions_passthrough_unchanged():
    payload = {"basis": "SOCRATES-derived, predicted, not observed", "items": []}

    def handler(request):
        assert request.url.path == "/conjunctions"
        assert request.url.params["risk"] == "high"
        return httpx.Response(200, json=payload)

    _use_upstream(handler)
    response = client.get("/api/conjunctions?risk=high&limit=5")
    assert response.status_code == 200
    assert response.json() == payload


def test_unknown_satellite_is_404():
    _use_upstream(lambda r: httpx.Response(404, json={"detail": "Satellite not found"}))
    response = client.get("/api/satellites/1/position")
    assert response.status_code == 404


def test_ml_down_gives_502():
    def handler(request):
        raise httpx.ConnectError("down")

    _use_upstream(handler)
    assert client.get("/api/stats").status_code == 502


def test_health_never_500_when_ml_down():
    def handler(request):
        raise httpx.ConnectError("down")

    _use_upstream(handler)
    body = client.get("/api/health").json()
    assert body["status"] == "degraded" and body["ml_api"] == "unreachable"

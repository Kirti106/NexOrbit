"""Proxy routes: /api/* -> ML API. JSON is returned unchanged, so every
response keeps model_version, generated_at, risk_tier, is_artifact and basis."""
from typing import Literal

from fastapi import APIRouter, Query

from ..services.ml_client import ml_get

router = APIRouter(prefix="/api", tags=["ML"])


@router.get("/satellites")
async def list_satellites(
    type: str | None = None,
    q: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
):
    return await ml_get("/satellites", {"type": type, "q": q, "limit": limit})


@router.get("/satellites/live")
async def live_satellites(limit: int = Query(default=500, ge=1, le=500)):
    return await ml_get("/satellites/live", {"limit": limit})


@router.get("/satellites/{norad_id}/position")
async def satellite_position(norad_id: int, time: str | None = None):
    return await ml_get(f"/satellites/{norad_id}/position", {"time": time})


@router.get("/satellites/{norad_id}/ground-track")
async def satellite_ground_track(
    norad_id: int,
    hours: float = Query(default=3, ge=0.25, le=24),
    step_s: int = Query(default=60, ge=10, le=3600),
):
    return await ml_get(
        f"/satellites/{norad_id}/ground-track", {"hours": hours, "step_s": step_s}
    )


@router.get("/conjunctions")
async def conjunctions(
    risk: Literal["low", "medium", "high"] | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    min_tca: str | None = None,
    include_artifacts: bool = False,
):
    return await ml_get(
        "/conjunctions",
        {
            "risk": risk,
            "limit": limit,
            "min_tca": min_tca,
            "include_artifacts": "true" if include_artifacts else None,
        },
    )


@router.get("/stats")
async def stats():
    return await ml_get("/stats")


@router.get("/anomalies")
async def anomalies(limit: int = Query(default=100, ge=1, le=500)):
    return await ml_get("/anomalies", {"limit": limit})

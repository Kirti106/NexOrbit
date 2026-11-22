import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request, Response
from sqlalchemy.orm import Session

from ...config import Settings
from ...core.cache import apply_etag, cache
from ...db.session import get_db
from ...deps import settings_dependency
from ...repositories.satellites import get_satellite
from ...schemas import (
    GroundTrackResponse,
    LiveResponse,
    PositionResponse,
    ConjunctionList,
    SatelliteHistoryResponse,
    SatelliteItem,
    SatelliteList,
)
from ...services.ml_client import MLClient
from ...services.orbit import propagate_gp, propagate_tle
from ...services.satellites import (
    satellite_conjunctions as get_satellite_conjunctions,
    satellite_history as get_satellite_history,
    search_satellites,
    satellite_item,
)

router = APIRouter(prefix="/satellites", tags=["Satellites"])
logger = logging.getLogger(__name__)


def ml_client(request: Request, settings: Settings = Depends(settings_dependency)) -> MLClient:
    return MLClient(settings, request.app.state.ml_http)


@router.get("", response_model=SatelliteList, summary="Search satellite catalog")
def list_satellites(
    q: str | None = Query(default=None, max_length=120, examples=["ISS", "25544"]),
    object_type: str | None = Query(default=None, max_length=50),
    orbit_class: str | None = Query(default=None, pattern="^(LEO|MEO|GEO)$"),
    country: str | None = Query(default=None, max_length=100),
    sort: str = Query(default="name", pattern="^(name|-name|norad_id|-norad_id)$"),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    return search_satellites(
        db,
        q=q,
        object_type=object_type,
        orbit=orbit_class,
        country=country,
        sort=sort,
        limit=limit,
        offset=offset,
    )


@router.get("/live", response_model=LiveResponse, summary="Get current satellite positions")
async def live_positions(
    request: Request,
    response: Response,
    limit: int = Query(default=500, ge=1, le=500),
    settings: Settings = Depends(settings_dependency),
    client: MLClient = Depends(ml_client),
):
    cache_key = f"live:{limit}"
    cached = cache.get(cache_key)
    if cached is not None:
        not_modified = apply_etag(request, response, cached, min(max(settings.cache_ttl, 5), 10))
        return not_modified or cached
    try:
        result = await client.get("/satellites/live", {"limit": limit})
        result["degraded"] = False
    except Exception:
        logger.exception("ML live positions request failed")
        result = {
            "generated_at": datetime.now(timezone.utc),
            "frame": "TEME position converted to geodetic",
            "items": [],
            "degraded": True,
        }
    cache.set(cache_key, result, min(max(settings.cache_ttl, 5), 10))
    not_modified = apply_etag(
        request, response, result, min(max(settings.cache_ttl, 5), 10)
    )
    return not_modified or result


@router.get("/{norad_id}", response_model=SatelliteItem, summary="Get satellite catalog details")
def get_satellite_details(norad_id: int, db: Session = Depends(get_db)):
    if norad_id <= 0:
        raise HTTPException(status_code=422, detail={"code": "invalid_norad_id", "message": "NORAD ID must be positive"})
    satellite, elements = get_satellite(db, norad_id)
    if satellite is None:
        raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Satellite not found"})
    return satellite_item(satellite, elements)


@router.get(
    "/{norad_id}/history",
    response_model=SatelliteHistoryResponse,
    summary="Get recent GP element history",
)
def satellite_history(
    norad_id: int = Path(gt=0),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    result = get_satellite_history(db, norad_id, limit)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "not_found", "message": "Satellite not found"},
        )
    return result


@router.get(
    "/{norad_id}/conjunctions",
    response_model=ConjunctionList,
    summary="List predicted conjunctions for one satellite",
)
def satellite_conjunctions(
    norad_id: int = Path(gt=0),
    risk_tier: str | None = Query(default=None, pattern="^(low|medium|high)$"),
    severity: str | None = Query(
        default=None, pattern="^(critical|high|medium|low|unknown)$"
    ),
    tca_from: datetime | None = None,
    tca_to: datetime | None = None,
    include_artifacts: bool = False,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    if (tca_from and tca_from.utcoffset() is None) or (
        tca_to and tca_to.utcoffset() is None
    ):
        raise HTTPException(
            status_code=422,
            detail={
                "code": "invalid_timestamp",
                "message": "TCA filters must include a UTC offset",
            },
        )
    if tca_from and tca_to and tca_from > tca_to:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "invalid_tca_range",
                "message": "tca_from must not be later than tca_to",
            },
        )
    result = get_satellite_conjunctions(
        db,
        norad_id,
        risk_tier=risk_tier,
        severity=severity,
        tca_from=tca_from,
        tca_to=tca_to,
        include_artifacts=include_artifacts,
        limit=limit,
        offset=offset,
    )
    if result is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "not_found", "message": "Satellite not found"},
        )
    return result


@router.get("/{norad_id}/position", response_model=PositionResponse, summary="Propagate satellite position")
async def satellite_position(
    norad_id: int,
    time: datetime | None = Query(default=None, examples=["2026-11-22T00:00:00Z"]),
    db: Session = Depends(get_db),
    client: MLClient = Depends(ml_client),
):
    if norad_id <= 0:
        raise HTTPException(status_code=422, detail={"code": "invalid_norad_id", "message": "NORAD ID must be positive"})
    if time is not None and time.utcoffset() is None:
        raise HTTPException(
            status_code=422,
            detail={"code": "invalid_timestamp", "message": "time must include a UTC offset"},
        )
    timestamp = time or datetime.now(timezone.utc)
    try:
        data = await client.get(f"/satellites/{norad_id}/position", {"time": timestamp.isoformat()})
        return {**data, "degraded": False}
    except Exception:
        logger.exception("ML position request failed for NORAD %s", norad_id)
        satellite, elements = get_satellite(db, norad_id)
        if satellite is None:
            raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Satellite not found"})
        if (not satellite.line1 or not satellite.line2) and elements is None:
            raise HTTPException(status_code=503, detail={"code": "ml_unavailable", "message": "Position service is unavailable and no local orbital elements are stored"})
        try:
            result = (
                propagate_tle(satellite.line1, satellite.line2, timestamp)
                if satellite.line1 and satellite.line2
                else propagate_gp(elements, timestamp)
            )
        except ValueError as exc:
            raise HTTPException(status_code=422, detail={"code": "propagation_failed", "message": str(exc)}) from exc
        return {
            "norad_id": norad_id,
            "name": satellite.object_name,
            "timestamp": timestamp,
            "frame": "TEME",
            **result,
            "degraded": True,
        }


@router.get("/{norad_id}/ground-track", response_model=GroundTrackResponse, summary="Get predicted ground track")
async def ground_track(
    norad_id: int,
    hours: float = Query(default=3, ge=0.25, le=24),
    step_s: int = Query(default=60, ge=10, le=3600),
    client: MLClient = Depends(ml_client),
):
    if norad_id <= 0:
        raise HTTPException(status_code=422, detail={"code": "invalid_norad_id", "message": "NORAD ID must be positive"})
    try:
        result = await client.get(
            f"/satellites/{norad_id}/ground-track",
            {"hours": hours, "step_s": step_s},
        )
        return {**result, "degraded": False}
    except Exception as exc:
        logger.exception("ML ground-track request failed for NORAD %s", norad_id)
        status_code = getattr(getattr(exc, "response", None), "status_code", None)
        if status_code == 404:
            raise HTTPException(
                status_code=404,
                detail={"code": "not_found", "message": "Satellite not found"},
            ) from exc
        raise HTTPException(
            status_code=503,
            detail={"code": "ml_unavailable", "message": "Ground-track service is unavailable"},
        ) from exc

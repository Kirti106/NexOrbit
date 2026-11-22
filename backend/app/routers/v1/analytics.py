import logging
from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from sqlalchemy.orm import Session

from ...config import Settings
from ...core.cache import apply_etag
from ...db.session import get_db
from ...deps import settings_dependency
from ...schemas import (
    AnalyticsResponse,
    AnomalyList,
    ConjunctionList,
    MetaResponse,
    StatsResponse,
)
from ...services.analytics import get_analytics, get_meta, get_stats
from ...services.conjunctions import search_conjunctions
from ...services.ml_client import MLClient

router = APIRouter(tags=["Analytics"])
logger = logging.getLogger(__name__)


def ml_client(request: Request, settings: Settings = Depends(settings_dependency)) -> MLClient:
    return MLClient(settings, request.app.state.ml_http)


@router.get("/stats", response_model=StatsResponse, summary="Get catalog and data freshness statistics")
def stats(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    settings: Settings = Depends(settings_dependency),
):
    result = get_stats(db, settings.cache_ttl)
    not_modified = apply_etag(request, response, result, settings.cache_ttl)
    return not_modified or result


@router.get("/analytics", response_model=AnalyticsResponse, summary="Get real orbital analytics")
def analytics(
    request: Request,
    response: Response,
    period: Literal["7D", "30D", "90D", "1Y"] = "30D",
    db: Session = Depends(get_db),
    settings: Settings = Depends(settings_dependency),
):
    result = get_analytics(db, period, settings.cache_ttl)
    not_modified = apply_etag(request, response, result, settings.cache_ttl)
    return not_modified or result


@router.get("/meta", response_model=MetaResponse, summary="Describe API data and freshness")
def meta(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    settings: Settings = Depends(settings_dependency),
):
    result = get_meta(db, request.app.version, settings.cache_ttl)
    not_modified = apply_etag(request, response, result, settings.cache_ttl)
    return not_modified or result


@router.get("/alerts", response_model=ConjunctionList, summary="List predicted conjunction alerts")
def alerts(
    risk_tier: str | None = Query(default=None, pattern="^(low|medium|high)$"),
    severity: str | None = Query(
        default=None, pattern="^(critical|high|medium|low|unknown)$"
    ),
    tca_from: datetime | None = None,
    tca_to: datetime | None = None,
    norad_id: int | None = Query(default=None, gt=0),
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
    return search_conjunctions(
        db,
        risk_tier=risk_tier,
        severity=severity,
        tca_from=tca_from,
        tca_to=tca_to,
        norad_id=norad_id,
        include_artifacts=include_artifacts,
        limit=limit,
        offset=offset,
    )


@router.get("/anomalies", response_model=AnomalyList, summary="List unusual orbit profiles")
async def anomalies(
    limit: int = Query(default=100, ge=1, le=500),
    client: MLClient = Depends(ml_client),
):
    try:
        result = await client.get("/anomalies", {"limit": min(max(limit, 1), 500)})
        result["degraded"] = False
        result["basis"] = "unusual orbit profile, not maneuver detection"
        return result
    except Exception:
        logger.exception("ML anomaly service request failed")
        return {
            "basis": "unusual orbit profile, not maneuver detection",
            "items": [],
            "degraded": True,
        }

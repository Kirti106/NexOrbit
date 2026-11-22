import logging
from datetime import datetime, timezone

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ...db.session import get_db
from ...deps import ml_http_dependency
from ...schemas import HealthResponse, ReadyResponse
from ...repositories.system import database_is_available, required_tables_available

router = APIRouter(tags=["System"])
logger = logging.getLogger(__name__)


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Check API, database, and ML service health",
)
async def health(
    db: Session = Depends(get_db),
    ml_http: httpx.AsyncClient = Depends(ml_http_dependency),
):
    try:
        database_is_available(db)
        database_status = "healthy"
    except Exception:
        logger.exception("Database health check failed")
        database_status = "unavailable"
    try:
        response = await ml_http.get("/health")
        response.raise_for_status()
        ml_status = "healthy"
    except (httpx.HTTPError, RuntimeError):
        logger.exception("ML health check failed")
        ml_status = "unavailable"
    overall = "healthy" if database_status == ml_status == "healthy" else "degraded"
    return {
        "status": overall,
        "database": database_status,
        "ml": ml_status,
        "checked_at": datetime.now(timezone.utc),
    }


@router.get("/ready", response_model=ReadyResponse, summary="Check whether the API can serve requests")
def ready(db: Session = Depends(get_db)):
    database_is_available(db)
    missing = [
        table
        for table, exists in required_tables_available(db).items()
        if not exists
    ]
    if missing:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "database_not_ready",
                "message": f"Required database tables are missing: {', '.join(missing)}",
            },
        )
    return {"status": "ready"}

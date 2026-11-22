import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ...config import Settings
from ...db.session import get_db
from ...deps import require_admin, settings_dependency
from ...schemas import SyncResponse
from ...services.sync import sync_conjunctions, sync_gp

router = APIRouter(prefix="/admin/sync", tags=["Administration"])
logger = logging.getLogger(__name__)


@router.post("/gp", response_model=SyncResponse, dependencies=[Depends(require_admin)], summary="Synchronize CelesTrak GP data")
async def sync_gp_endpoint(
    group: str = Query(default="active", pattern="^[a-zA-Z0-9_-]+$"),
    db: Session = Depends(get_db),
):
    try:
        return await sync_gp(db, group)
    except Exception as exc:
        logger.exception("GP synchronization failed")
        raise HTTPException(
            status_code=502,
            detail={"code": "gp_sync_failed", "message": str(exc)},
        ) from exc


@router.post("/conjunctions", response_model=SyncResponse, dependencies=[Depends(require_admin)], summary="Synchronize SOCRATES conjunction predictions")
async def sync_conjunctions_endpoint(
    db: Session = Depends(get_db),
    settings: Settings = Depends(settings_dependency),
):
    try:
        return await sync_conjunctions(db, settings)
    except RuntimeError as exc:
        raise HTTPException(
            status_code=503,
            detail={"code": "socrates_unavailable", "message": str(exc)},
        ) from exc
    except Exception as exc:
        logger.exception("Conjunction synchronization failed")
        raise HTTPException(
            status_code=502,
            detail={"code": "conjunction_sync_failed", "message": str(exc)},
        ) from exc

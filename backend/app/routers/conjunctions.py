from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..services.conjunctions import list_conjunctions

router = APIRouter(prefix="/api/conjunctions", tags=["Conjunctions"])


@router.get("")
def get_conjunctions(
    risk: str | None = Query(default=None, pattern="^(low|medium|high)$"),
    tca_from: datetime | None = None,
    tca_to: datetime | None = None,
    norad_id: int | None = Query(default=None, ge=1),
    include_artifacts: bool = False,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    if tca_from and tca_to and tca_from > tca_to:
        raise HTTPException(status_code=422, detail="tca_from must not be after tca_to")
    return list_conjunctions(
        db,
        risk=risk,
        tca_from=tca_from,
        tca_to=tca_to,
        norad_id=norad_id,
        include_artifacts=include_artifacts,
        limit=limit,
        offset=offset,
    )

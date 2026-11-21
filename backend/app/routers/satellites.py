from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Satellite
from ..schemas import PositionOut, SatelliteListOut, SyncOut
from ..services.celestrak import sync_tle_group
from ..services.orbit import propagate_tle

router = APIRouter(prefix="/api/satellites", tags=["Satellites"])


@router.get("", response_model=SatelliteListOut)
def list_satellites(
    search: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    statement = select(Satellite)
    count_statement = select(func.count()).select_from(Satellite)

    if search:
        condition = or_(
            Satellite.name.ilike(f"%{search}%"),
            func.cast(Satellite.norad_id, str).ilike(f"%{search}%"),
        )
        statement = statement.where(condition)
        count_statement = count_statement.where(condition)

    total = db.scalar(count_statement) or 0
    items = db.scalars(
        statement.order_by(Satellite.name).offset(offset).limit(limit)
    ).all()
    return {"total": total, "items": items}


@router.get("/{norad_id}")
def get_satellite(norad_id: int, db: Session = Depends(get_db)):
    satellite = db.scalar(
        select(Satellite).where(Satellite.norad_id == norad_id)
    )
    if satellite is None:
        raise HTTPException(status_code=404, detail="Satellite not found")
    return satellite


@router.get("/{norad_id}/position", response_model=PositionOut)
def get_satellite_position(
    norad_id: int,
    at: datetime | None = None,
    db: Session = Depends(get_db),
):
    satellite = db.scalar(
        select(Satellite).where(Satellite.norad_id == norad_id)
    )
    if satellite is None:
        raise HTTPException(status_code=404, detail="Satellite not found")

    timestamp = at or datetime.now(timezone.utc)
    try:
        result = propagate_tle(satellite.line1, satellite.line2, timestamp)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return {
        "norad_id": satellite.norad_id,
        "name": satellite.name,
        "timestamp": timestamp,
        "frame": "TEME",
        "units": "km and km/s",
        **result,
    }


@router.post("/sync", response_model=SyncOut)
def sync_satellites(
    group: str = Query(default="stations", pattern="^[a-zA-Z0-9_-]+$"),
    db: Session = Depends(get_db),
):
    try:
        received, changed = sync_tle_group(db, group)
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Could not retrieve CelesTrak data: {exc}",
        ) from exc

    return {
        "source": "CelesTrak",
        "group": group,
        "received": received,
        "inserted_or_updated": changed,
        "message": "TLE data imported. Positions are estimates based on the supplied element epochs.",
    }

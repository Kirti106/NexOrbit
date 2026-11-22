import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..config import get_settings
from ..database import get_db
from ..services.celestrak import sync_tle_group
from ..services.satellites import satellite_detail, search_satellites

router = APIRouter(prefix="/api/satellites", tags=["Satellites"])


@router.get("")
def list_satellites(
    q: str | None = None,
    object_type: str | None = None,
    orbit_class: str | None = Query(default=None, pattern="^(LEO|MEO|GEO)$"),
    country: str | None = None,
    sort: str = Query(default="name_asc", pattern="^(name_asc|name_desc)$"),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    return search_satellites(
        db,
        q=q,
        object_type=object_type,
        orbit_class=orbit_class,
        country=country,
        sort=sort,
        limit=limit,
        offset=offset,
    )


@router.get("/live")
def live_positions(limit: int = Query(default=100, ge=1, le=500)):
    return _get_ml_data("/satellites/live", {"limit": limit})


@router.post("/sync")
def sync_satellites(
    group: str = Query(default="active", pattern="^[a-zA-Z0-9_-]+$"),
    db: Session = Depends(get_db),
):
    try:
        received, changed, skipped = sync_tle_group(db, group)
    except RuntimeError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Could not retrieve CelesTrak data: {exc}",
        ) from exc
    return {
        "source": "CelesTrak",
        "group": group,
        "received": received,
        "inserted_or_updated": changed,
        "skipped": skipped,
    }


@router.get("/{norad_id}")
def get_satellite(norad_id: int, db: Session = Depends(get_db)):
    satellite = satellite_detail(db, norad_id)
    if satellite is None:
        raise HTTPException(status_code=404, detail="Satellite not found")
    return satellite


@router.get("/{norad_id}/position")
def get_satellite_position(norad_id: int, time: str | None = None):
    return _get_ml_data(
        f"/satellites/{norad_id}/position",
        {"time": time} if time else None,
    )


def _get_ml_data(path: str, params: dict | None = None):
    url = f"{get_settings().ml_api_url.rstrip('/')}{path}"
    try:
        response = httpx.get(url, params=params, timeout=httpx.Timeout(8, connect=2))
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=exc.response.status_code,
            detail="The orbital propagation service rejected the request",
        ) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=503,
            detail="The orbital propagation service is unavailable",
        ) from exc
    return response.json()

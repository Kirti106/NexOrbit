from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from ...db.session import get_db
from ...config import Settings
from ...core.cache import apply_etag
from ...deps import settings_dependency
from ...schemas import (
    ConjunctionItem,
    ConjunctionList,
    ConjunctionSummaryResponse,
)
from ...services.analytics import get_conjunction_summary
from ...services.conjunctions import (
    conjunction_details,
    search_conjunctions,
    stream_conjunction_export,
)

router = APIRouter(prefix="/conjunctions", tags=["Conjunctions"])


@router.get("", response_model=ConjunctionList, summary="Search predicted conjunctions")
def conjunctions(
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
            detail={"code": "invalid_timestamp", "message": "TCA filters must include a UTC offset"},
        )
    if tca_from and tca_to and tca_from > tca_to:
        raise HTTPException(
            status_code=422,
            detail={"code": "invalid_tca_range", "message": "tca_from must not be later than tca_to"},
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


@router.get(
    "/summary",
    response_model=ConjunctionSummaryResponse,
    summary="Summarize predicted conjunctions by risk and severity",
)
def conjunction_summary(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    settings: Settings = Depends(settings_dependency),
):
    result = get_conjunction_summary(db, settings.cache_ttl)
    not_modified = apply_etag(request, response, result, settings.cache_ttl)
    return not_modified or result


@router.get(
    "/export",
    response_model=list[ConjunctionItem],
    summary="Stream predicted conjunctions as CSV or JSON",
    responses={
        200: {
            "content": {
                "text/csv": {"schema": {"type": "string", "format": "binary"}},
                "application/json": {
                    "schema": {"type": "array", "items": {"$ref": "#/components/schemas/ConjunctionItem"}}
                },
            }
        }
    },
)
def export_conjunctions(
    format: Literal["csv", "json"] = "json",
    risk_tier: str | None = Query(default=None, pattern="^(low|medium|high)$"),
    severity: str | None = Query(
        default=None, pattern="^(critical|high|medium|low|unknown)$"
    ),
    tca_from: datetime | None = None,
    tca_to: datetime | None = None,
    norad_id: int | None = Query(default=None, gt=0),
    include_artifacts: bool = False,
    limit: int = Query(default=5000, ge=1, le=5000),
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
    stream = stream_conjunction_export(
        db,
        format=format,
        risk_tier=risk_tier,
        severity=severity,
        tca_from=tca_from,
        tca_to=tca_to,
        norad_id=norad_id,
        include_artifacts=include_artifacts,
        limit=limit,
        offset=offset,
    )
    content_type = "text/csv" if format == "csv" else "application/json"
    return StreamingResponse(
        stream,
        media_type=content_type,
        headers={"Content-Disposition": f'attachment; filename="conjunctions.{format}"'},
    )


@router.get("/{conjunction_id}", response_model=ConjunctionItem, summary="Get predicted conjunction details")
def conjunction_detail(conjunction_id: int, db: Session = Depends(get_db)):
    result = conjunction_details(db, conjunction_id)
    if result is None:
        raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Conjunction not found"})
    return result

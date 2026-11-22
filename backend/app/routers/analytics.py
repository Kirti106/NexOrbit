from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..services.analytics import analytics, stats

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


@router.get("")
def get_analytics(
    period: str = Query(default="30D", pattern="^(7D|30D|90D|1Y)$"),
    db: Session = Depends(get_db),
):
    return analytics(db, period)


@router.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    return stats(db)

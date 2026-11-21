from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Satellite

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


@router.get("")
def get_analytics(db: Session = Depends(get_db)):
    total = db.scalar(select(func.count()).select_from(Satellite)) or 0

    return {
        "total_objects": total,
        "active_satellites": None,
        "debris_objects": None,
        "upcoming_conjunctions": None,
        "data_status": "loaded" if total else "empty",
        "note": (
            "The initial CelesTrak import does not classify every object as active "
            "or debris and does not calculate conjunction probability. Those fields "
            "are null until validated classification and screening modules are added."
        ),
    }

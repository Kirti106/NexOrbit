from sqlalchemy import and_, or_

from ..models import Conjunction


def risk_tier(
    max_prob: float | None,
    min_range_km: float | None,
    is_artifact: bool,
) -> str:
    probability = max_prob or 0.0
    if is_artifact:
        return "low"
    if probability >= 1e-3 or (
        probability >= 1e-5
        and min_range_km is not None
        and min_range_km <= 50
    ):
        return "high"
    if probability >= 1e-5:
        return "medium"
    return "low"


def tier_filter(tier: str):
    high = and_(
        Conjunction.is_constellation_artifact.is_(False),
        or_(
            Conjunction.max_prob >= 1e-3,
            and_(
                Conjunction.max_prob >= 1e-5,
                Conjunction.min_range_km <= 50,
            ),
        ),
    )
    medium = and_(
        Conjunction.is_constellation_artifact.is_(False),
        Conjunction.max_prob >= 1e-5,
        ~high,
    )
    low = or_(
        Conjunction.is_constellation_artifact.is_(True),
        Conjunction.max_prob < 1e-5,
        Conjunction.max_prob.is_(None),
    )
    return {"high": high, "medium": medium, "low": low}[tier]

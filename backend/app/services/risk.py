def risk_tier(
    max_prob: float | None,
    min_range_km: float | None,
    is_artifact: bool,
) -> str:
    probability = max_prob or 0.0
    if is_artifact:
        return "low"
    if probability >= 1e-3 or (
        probability >= 1e-5 and (min_range_km is not None and min_range_km <= 50)
    ):
        return "high"
    if probability >= 1e-5:
        return "medium"
    return "low"

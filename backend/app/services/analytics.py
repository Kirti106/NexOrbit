from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from ..core.cache import cache
from ..repositories import catalog
from ..repositories.analytics import conjunction_daily_data, statistics_data
from ..services.risk import risk_tier

PERIOD_DAYS = {"7D": 7, "30D": 30, "90D": 90, "1Y": 365}


def get_stats(db: Session, ttl: int) -> dict:
    cached = cache.get("stats")
    if cached is not None:
        return cached
    data = statistics_data(db)
    total = data["total"]
    by_type = data["by_type"]
    by_orbit = data["by_orbit"]
    conjunction_count = data["conjunction_count"]
    result = {
        "generated_at": datetime.now(timezone.utc),
        "total_objects": total or None,
        "counts_by_object_type": by_type or None,
        "counts_by_orbit_class": by_orbit if sum(by_orbit.values()) else None,
        "conjunctions": conjunction_count or None,
        "high_risk_conjunctions": data["high_count"] if conjunction_count else None,
        "data_freshness": {
            "gp_fetched_at": data["gp_fresh"],
            "conjunctions_fetched_at": data["conjunction_fresh"],
        },
        "unavailable_reasons": {
            **({"catalog": "No satellite catalog records are available."} if total == 0 else {}),
            **({"orbit_class": "No orbital elements are available."} if not sum(by_orbit.values()) else {}),
            **({"conjunctions": "No conjunction data is available."} if conjunction_count == 0 else {}),
        },
    }
    cache.set("stats", result, ttl)
    return result


def get_analytics(db: Session, period: str, ttl: int) -> dict:
    cache_key = f"analytics:{period}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached
    data = statistics_data(db)
    days = PERIOD_DAYS[period]
    since = datetime.now(timezone.utc) - timedelta(days=days)
    daily: dict[str, dict[str, int]] = {}
    for row in conjunction_daily_data(db, since):
        day = row.day.isoformat() if hasattr(row.day, "isoformat") else str(row.day)
        tiers = daily.setdefault(day, {"low": 0, "medium": 0, "high": 0, "total": 0})
        tier = risk_tier(row.max_prob, row.min_range_km, row.is_constellation_artifact)
        tiers[tier] += row.count
        tiers["total"] += row.count
    result = {
        "period": period,
        "generated_at": datetime.now(timezone.utc),
        "conjunctions_per_day": [
            {"date": day, **daily[day]} for day in sorted(daily)
        ] or None,
        "counts_by_object_type": data["by_type"] or None,
        "counts_by_orbit_class": (
            data["by_orbit"] if sum(data["by_orbit"].values()) else None
        ),
        "data_freshness": {
            "gp_fetched_at": data["gp_fresh"],
            "conjunctions_fetched_at": data["conjunction_fresh"],
        },
        "unavailable_reasons": {
            **({"conjunctions_per_day": "No conjunction records in this period."} if not daily else {}),
            **({"orbit_class": "No orbital elements are available."} if not sum(data["by_orbit"].values()) else {}),
        },
    }
    cache.set(cache_key, result, ttl)
    return result


def get_conjunction_summary(db: Session, ttl: int) -> dict:
    cached = cache.get("conjunction-summary")
    if cached is not None:
        return cached
    now = datetime.now(timezone.utc)
    result = {
        "generated_at": now,
        "basis": "predicted, not observed",
        "all": catalog.conjunction_summary_counts(db),
        "next_7_days": catalog.conjunction_summary_counts(
            db,
            tca_from=now,
            tca_to=now + timedelta(days=7),
        ),
    }
    cache.set("conjunction-summary", result, ttl)
    return result


def get_meta(db: Session, api_version: str, ttl: int) -> dict:
    cache_key = f"meta:{api_version}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached
    result = {
        "api_version": api_version,
        "generated_at": datetime.now(timezone.utc),
        "data_freshness": catalog.meta_snapshot(db),
        "data_basis": {
            "conjunctions": "SOCRATES predictions, not observed collisions.",
            "max_prob": "A secondary SOCRATES estimate, never a real collision probability.",
            "anomalies": "Unusual orbit profile, not maneuver detection.",
            "orbit_class": "Approximate classification derived from orbital elements.",
            "timestamps": "All timestamps are UTC.",
        },
    }
    cache.set(cache_key, result, ttl)
    return result

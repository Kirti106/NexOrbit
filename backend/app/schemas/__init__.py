from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class APIModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class SatelliteItem(APIModel):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [{
                "norad_id": 25544,
                "name": "ISS (ZARYA)",
                "object_type": "PAYLOAD",
                "country": "US",
                "orbit_class": "LEO",
                "inclination": 51.6,
                "eccentricity": 0.0007,
                "period_minutes": 92.9,
                "apogee_km": 425.0,
                "perigee_km": 415.0,
                "launch_date": "1998-11-20T00:00:00Z",
                "status": "operational",
                "epoch": "2026-11-22T00:00:00Z",
            }]
        },
    )
    norad_id: int
    name: str
    object_type: str | None = None
    country: str | None = None
    orbit_class: Literal["LEO", "MEO", "GEO"] | None = None
    inclination: float | None = None
    eccentricity: float | None = None
    period_minutes: float | None = None
    apogee_km: float | None = None
    perigee_km: float | None = None
    launch_date: datetime | None = None
    status: str | None = None
    epoch: datetime | None = None


class SatelliteList(APIModel):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={"examples": [{"total": 1, "items": [{"norad_id": 25544, "name": "ISS (ZARYA)"}]}]},
    )
    total: int
    items: list[SatelliteItem]


class PositionResponse(APIModel):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={"examples": [{
            "norad_id": 25544,
            "name": "ISS (ZARYA)",
            "timestamp": "2026-11-22T00:00:00Z",
            "frame": "TEME",
            "position": {"x": 1.0, "y": 2.0, "z": 3.0},
            "velocity": {"x": 4.0, "y": 5.0, "z": 6.0},
            "altitude_km": 420.0,
            "speed_kms": 8.77,
            "degraded": False,
        }]},
    )
    norad_id: int
    name: str
    timestamp: datetime
    frame: str
    position: dict[str, float]
    velocity: dict[str, float]
    altitude_km: float | None = None
    speed_kms: float | None = None
    degraded: bool = False


class GroundTrackPoint(APIModel):
    timestamp: datetime
    latitude: float
    longitude: float
    altitude_km: float


class GroundTrackResponse(APIModel):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={"examples": [{
            "norad_id": 25544,
            "points": [{"timestamp": "2026-11-22T00:00:00Z", "latitude": 10.0, "longitude": -20.0, "altitude_km": 420.0}],
            "degraded": False,
        }]},
    )
    norad_id: int
    points: list[GroundTrackPoint]
    degraded: bool = False


class LivePosition(APIModel):
    norad_id: int
    name: str
    latitude: float
    longitude: float
    altitude_km: float


class LiveResponse(APIModel):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={"examples": [{
            "generated_at": "2026-11-22T00:00:00Z",
            "frame": "TEME position converted to geodetic",
            "items": [{"norad_id": 25544, "name": "ISS (ZARYA)", "latitude": 10.0, "longitude": -20.0, "altitude_km": 420.0}],
            "degraded": False,
        }]},
    )
    generated_at: datetime
    frame: str
    items: list[LivePosition]
    degraded: bool = False


class ConjunctionItem(APIModel):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={"examples": [{
            "id": 1, "norad_id_1": 25544, "norad_id_2": 48291,
            "object_name_1": "ISS (ZARYA)", "object_name_2": "OBJECT 48291",
            "tca": "2026-11-23T12:00:00Z", "min_range_km": 8.0,
            "rel_speed_kms": 10.2, "max_prob": 0.0001, "risk_tier": "high",
            "is_artifact": False, "fetched_at": "2026-11-22T00:00:00Z",
            "basis": "predicted, not observed",
        }]},
    )
    id: int
    norad_id_1: int
    norad_id_2: int
    object_name_1: str | None
    object_name_2: str | None
    tca: datetime
    min_range_km: float | None
    rel_speed_kms: float | None
    max_prob: float | None = Field(
        description="SOCRATES secondary estimate; not an actual collision probability."
    )
    risk_tier: str
    is_artifact: bool
    fetched_at: datetime
    basis: str = "predicted, not observed"


class ConjunctionList(APIModel):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={"examples": [{
            "total": 1, "basis": "predicted, not observed",
            "fetched_at": "2026-11-22T00:00:00Z", "items": [],
        }]},
    )
    total: int
    items: list[ConjunctionItem]
    basis: str = "predicted, not observed"
    fetched_at: datetime | None = None


class GPHistoryItem(APIModel):
    epoch: datetime
    mean_motion: float | None = None
    eccentricity: float | None = None
    inclination: float | None = None
    bstar: float | None = None


class SatelliteHistoryResponse(APIModel):
    norad_id: int
    items: list[GPHistoryItem]


class ConjunctionSummaryCounts(APIModel):
    total: int
    by_risk_tier: dict[str, int]
    by_severity: dict[str, int]


class ConjunctionSummaryResponse(APIModel):
    generated_at: datetime
    basis: str = "predicted, not observed"
    all: ConjunctionSummaryCounts
    next_7_days: ConjunctionSummaryCounts


class MetaResponse(APIModel):
    api_version: str
    generated_at: datetime
    data_freshness: dict[str, datetime | None]
    data_basis: dict[str, str]


class StatsResponse(APIModel):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={"examples": [{
            "generated_at": "2026-11-22T00:00:00Z", "total_objects": None,
            "counts_by_object_type": None, "counts_by_orbit_class": None,
            "conjunctions": None, "high_risk_conjunctions": None,
            "data_freshness": {"gp_fetched_at": None, "conjunctions_fetched_at": None},
            "unavailable_reasons": {"catalog": "No satellite catalog records are available."},
        }]},
    )
    generated_at: datetime
    total_objects: int | None
    counts_by_object_type: dict[str, int] | None
    counts_by_orbit_class: dict[str, int] | None
    conjunctions: int | None
    high_risk_conjunctions: int | None
    data_freshness: dict[str, datetime | None]
    unavailable_reasons: dict[str, str] = Field(default_factory=dict)


class AnalyticsResponse(APIModel):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={"examples": [{
            "period": "7D", "generated_at": "2026-11-22T00:00:00Z",
            "conjunctions_per_day": None,
            "counts_by_object_type": None, "counts_by_orbit_class": None,
            "data_freshness": {"gp_fetched_at": None, "conjunctions_fetched_at": None},
            "unavailable_reasons": {"conjunctions_per_day": "No conjunction records in this period."},
        }]},
    )
    period: str
    generated_at: datetime
    conjunctions_per_day: list[dict[str, Any]] | None
    counts_by_object_type: dict[str, int] | None
    counts_by_orbit_class: dict[str, int] | None
    data_freshness: dict[str, datetime | None]
    unavailable_reasons: dict[str, str] = Field(default_factory=dict)


class AnomalyList(APIModel):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={"examples": [{
            "basis": "unusual orbit profile, not maneuver detection",
            "items": [{"norad_id": 25544, "name": "ISS (ZARYA)", "score": 2.1, "top_feature": "eccentricity", "label": "unusual orbit profile"}],
            "degraded": False,
        }]},
    )
    basis: str = "unusual orbit profile, not maneuver detection"
    items: list[dict[str, Any]]
    degraded: bool = False


class SyncResponse(APIModel):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={"examples": [{
            "source": "CelesTrak", "received": 1, "inserted_or_updated": 1,
            "skipped": False, "message": "GP catalog and orbital elements were synchronized.",
        }]},
    )
    source: str
    received: int
    inserted_or_updated: int
    skipped: bool = False
    message: str


class HealthResponse(APIModel):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={"examples": [{
            "status": "healthy", "database": "healthy", "ml": "healthy",
            "checked_at": "2026-11-22T00:00:00Z",
        }]},
    )
    status: Literal["healthy", "degraded"]
    database: Literal["healthy", "unavailable"]
    ml: Literal["healthy", "unavailable"]
    checked_at: datetime


class ReadyResponse(APIModel):
    model_config = ConfigDict(from_attributes=True, json_schema_extra={"examples": [{"status": "ready"}]})
    status: Literal["ready"]

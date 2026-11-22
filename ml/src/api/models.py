from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class ResponseMeta(BaseModel):
    model_version: str = "2026-11-22-v1"
    generated_at: datetime


class HealthResponse(ResponseMeta):
    status: Literal["healthy", "degraded"]
    database: Literal["connected", "unavailable"]


class SatelliteResponse(ResponseMeta):
    norad_id: int
    name: str
    object_type: str
    owner_country: str | None = None
    launch_date: datetime | None = None
    decay_date: datetime | None = None
    rcs_size: str | None = None


class SatelliteListResponse(ResponseMeta):
    total: int
    items: list[SatelliteResponse]


class LivePosition(BaseModel):
    norad_id: int
    name: str
    object_type: str = "UNKNOWN"
    latitude: float
    longitude: float
    altitude_km: float


class LiveResponse(ResponseMeta):
    frame: Literal["TEME position converted to geodetic"]
    items: list[LivePosition]


class PositionResponse(ResponseMeta):
    norad_id: int
    name: str
    timestamp: datetime
    frame: Literal["TEME"]
    position: dict[str, float]
    velocity: dict[str, float]
    altitude_km: float | None = None
    speed_kms: float


class GroundTrackPoint(BaseModel):
    timestamp: datetime
    latitude: float
    longitude: float
    altitude_km: float


class GroundTrackResponse(ResponseMeta):
    norad_id: int
    points: list[GroundTrackPoint]


class ConjunctionResponse(BaseModel):
    norad_id_1: int
    norad_id_2: int
    object_name_1: str | None
    object_name_2: str | None
    tca: datetime
    min_range_km: float
    rel_speed_kms: float | None
    max_prob: float | None = Field(
        default=None,
        description="SOCRATES maximum-probability estimate; never presented as observed collision probability.",
    )
    risk_tier: Literal["low", "medium", "high"]
    is_artifact: bool
    fetched_at: datetime


class ConjunctionListResponse(ResponseMeta):
    basis: Literal["SOCRATES-derived, predicted, not observed"]
    items: list[ConjunctionResponse]


class StatsResponse(ResponseMeta):
    satellites_by_object_type: dict[str, int]
    tracked_satellites: int
    high_risk_conjunctions: int
    conjunctions: int
    debris_share: float
    gp_freshest_at: datetime | None
    socrates_fetched_at: datetime | None


class AnomalyResponse(BaseModel):
    norad_id: int
    name: str
    score: float
    top_feature: str
    label: Literal["unusual orbit profile"]


class AnomalyListResponse(ResponseMeta):
    basis: Literal["cross-sectional element profile, not maneuver detection"]
    items: list[AnomalyResponse]

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class SatelliteOut(BaseModel):
    norad_id: int
    name: str
    object_type: str | None = None
    country: str | None = None
    orbit_class: str | None = None
    updated_at: datetime | None = None


class SatelliteListOut(BaseModel):
    total: int
    items: list[SatelliteOut]


class OrbitalElements(BaseModel):
    inclination: float | None = None
    eccentricity: float | None = None
    period_minutes: float | None = None
    apogee_km: float | None = None
    perigee_km: float | None = None
    epoch: datetime | None = None


class SatelliteDetailOut(SatelliteOut):
    launch_date: datetime | None = None
    decay_date: datetime | None = None
    mission_info: dict[str, Any] | None = None
    latest_orbital_elements: OrbitalElements | None = None


class ConjunctionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    norad_id_1: int
    norad_id_2: int
    object_name_1: str | None = None
    object_name_2: str | None = None
    tca: datetime
    min_range_km: float | None = None
    rel_speed_kms: float | None = None
    max_prob: float | None = Field(
        default=None,
        description="SOCRATES maximum-probability estimate, not an observed collision probability.",
    )
    risk_tier: Literal["low", "medium", "high"]
    is_artifact: bool
    fetched_at: datetime | None = None


class ConjunctionListOut(BaseModel):
    total: int
    basis: Literal["predicted, not observed"] = "predicted, not observed"
    fetched_at: datetime | None = None
    items: list[ConjunctionOut]


class StatsOut(BaseModel):
    total_satellites: int | None
    satellites_by_object_type: dict[str, int] | None
    satellites_by_orbit_class: dict[str, int] | None
    conjunction_count: int | None
    data_freshness: dict[str, datetime | None] | None
    reason: str | None = None


class DailyConjunctionCount(BaseModel):
    date: datetime
    risk_tier: str
    count: int


class AnalyticsOut(BaseModel):
    period: str
    satellites_by_object_type: dict[str, int] | None
    satellites_by_orbit_class: dict[str, int] | None
    conjunctions_per_day: list[DailyConjunctionCount] | None
    data_freshness: dict[str, datetime | None] | None
    reason: str | None = None


class HealthOut(BaseModel):
    status: Literal["healthy", "degraded"]
    database: Literal["connected", "unavailable"]
    ml: Literal["connected", "unavailable"]


class ReadyOut(BaseModel):
    status: Literal["ready"]


class SyncOut(BaseModel):
    source: str
    received: int
    inserted_or_updated: int
    skipped: bool = False
    message: str


class ErrorBody(BaseModel):
    error: dict[str, str]


class MLProxyOut(BaseModel):
    model_config = ConfigDict(extra="allow")

    degraded: bool = False

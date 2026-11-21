from datetime import datetime
from pydantic import BaseModel, ConfigDict


class SatelliteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    norad_id: int
    name: str
    epoch: str | None = None
    object_type: str
    source: str
    updated_at: datetime


class SatelliteListOut(BaseModel):
    total: int
    items: list[SatelliteOut]


class SyncOut(BaseModel):
    source: str
    group: str
    received: int
    inserted_or_updated: int
    message: str


class PositionOut(BaseModel):
    norad_id: int
    name: str
    timestamp: datetime
    frame: str
    units: str
    position: dict[str, float]
    velocity: dict[str, float]

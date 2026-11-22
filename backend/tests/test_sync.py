from datetime import datetime, timezone
from unittest.mock import AsyncMock

import httpx
import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.config import Settings
from app.db.base import Base
from app.models.satellite import Conjunction, GPHistory, Satellite
from app.services.sync import sync_conjunctions, sync_gp


@pytest.mark.asyncio
async def test_gp_sync_upserts_and_observes_two_hour_cache(monkeypatch):
    engine = create_engine("sqlite://", poolclass=StaticPool)
    Base.metadata.create_all(engine)
    records = [{
        "NORAD_CAT_ID": "25544",
        "OBJECT_NAME": "ISS (ZARYA)",
        "OBJECT_TYPE": "PAYLOAD",
        "EPOCH": datetime.now(timezone.utc).isoformat(),
        "MEAN_MOTION": "15.5",
        "ECCENTRICITY": "0.001",
        "INCLINATION": "51.6",
    }]
    fetch = AsyncMock(
        return_value=httpx.Response(
            200,
            json=records,
            request=httpx.Request("GET", "https://celestrak.test"),
        )
    )
    monkeypatch.setattr("app.services.sync._fetch", fetch)
    with Session(engine) as db:
        first = await sync_gp(db, "active")
        second = await sync_gp(db, "active")
        assert first["inserted_or_updated"] == 1
        assert second["skipped"] is True
        assert fetch.await_count == 1
        assert db.scalar(select(func.count()).select_from(Satellite)) == 1
        assert db.scalar(select(func.count()).select_from(GPHistory)) == 1
    engine.dispose()


@pytest.mark.asyncio
async def test_conjunction_sync_is_idempotent_and_marks_artifacts(monkeypatch):
    engine = create_engine("sqlite://", poolclass=StaticPool)
    Base.metadata.create_all(engine)
    csv_body = (
        "NORAD_CAT_ID_1,OBJECT_NAME_1,DSE_1,NORAD_CAT_ID_2,OBJECT_NAME_2,"
        "DSE_2,TCA,TCA_RANGE,TCA_RELATIVE_SPEED,MAX_PROB,DILUTION\n"
        "1,STARLINK-100 [P],1.2,2,STARLINK-101 [+],1.3,"
        "2026-11-24 21:13:59.569,0.1,11.5,1.000E-4,0.02\n"
    )
    fetch = AsyncMock(
        return_value=httpx.Response(
            200,
            text=csv_body,
            request=httpx.Request("GET", "https://socrates.test/events.csv"),
        )
    )
    monkeypatch.setattr("app.services.sync._fetch", fetch)
    settings = Settings(database_url="sqlite://", socrates_url="https://socrates.test/events.csv")
    with Session(engine) as db:
        await sync_conjunctions(db, settings)
        await sync_conjunctions(db, settings)
        assert db.scalar(select(func.count()).select_from(Conjunction)) == 1
        event = db.scalar(select(Conjunction))
        assert event.is_constellation_artifact is True
        assert event.risk_tier == "low"
        assert event.risk_weight == 0.1
        assert event.dse_1 == 1.2
    engine.dispose()

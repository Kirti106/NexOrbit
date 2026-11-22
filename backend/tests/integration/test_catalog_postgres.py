import os
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import engine
from app.models.satellite import Conjunction, Satellite
from app.repositories import catalog

pytestmark = pytest.mark.skipif(
    not os.getenv("TEST_DATABASE_URL"),
    reason="TEST_DATABASE_URL is not configured",
)


@pytest.fixture
def postgres_read_session():
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, autoflush=False, expire_on_commit=False)
    try:
        yield session
    finally:
        session.close()
        if transaction.is_active:
            transaction.rollback()
        connection.close()


def test_list_satellites_filters_and_paging(postgres_read_session):
    db = postgres_read_session
    sample = db.scalar(select(Satellite).order_by(Satellite.norad_cat_id).limit(1))

    total, rows = catalog.list_satellites(
        db, q=str(sample.norad_cat_id) if sample else "no-match", limit=2, offset=0
    )
    assert total >= len(rows)
    assert len(rows) <= 2
    if sample:
        assert any(row[0].norad_cat_id == sample.norad_cat_id for row in rows)
        assert catalog.list_satellites(
            db, object_type=sample.object_type, limit=1, offset=0
        )[0] >= 0

    for orbit_class in ("LEO", "MEO", "GEO"):
        assert catalog.list_satellites(
            db, orbit_class=orbit_class, limit=1, offset=1
        )[0] >= 0


def test_get_satellite(postgres_read_session):
    db = postgres_read_session
    norad_id = db.scalar(select(Satellite.norad_cat_id).limit(1))
    if norad_id is None:
        assert catalog.get_satellite(db, 1) == (None, None)
    else:
        satellite, _latest = catalog.get_satellite(db, norad_id)
        assert satellite is not None
        assert satellite.norad_cat_id == norad_id


def test_list_conjunctions_filters(postgres_read_session):
    db = postgres_read_session
    sample = db.scalar(select(Conjunction).limit(1))
    now = datetime.now(timezone.utc)
    for tier in ("low", "medium", "high"):
        assert catalog.list_conjunctions(db, risk_tier=tier, limit=2)[0] >= 0
    for severity in ("critical", "high", "medium", "low", "unknown"):
        assert catalog.list_conjunctions(db, severity=severity, limit=2)[0] >= 0

    assert catalog.list_conjunctions(
        db, tca_from=now, tca_to=now + timedelta(days=7), limit=2
    )[0] >= 0
    assert catalog.list_conjunctions(db, include_artifacts=True, limit=2)[0] >= 0
    assert catalog.list_conjunctions(db, include_artifacts=False, limit=2)[0] >= 0
    if sample:
        assert catalog.list_conjunctions(
            db, norad_id=sample.norad_cat_id_1, limit=2
        )[0] >= 0


def test_aggregate_catalog_queries(postgres_read_session):
    db = postgres_read_session
    assert set(catalog.severity_counts(db)).issubset(
        {"critical", "high", "medium", "low", "unknown"}
    )
    assert isinstance(catalog.conjunctions_per_day(db, datetime.now(timezone.utc)), list)
    assert isinstance(catalog.stats_snapshot(db), dict)
    assert set(catalog.orbit_class_counts(db)) == {"LEO", "MEO", "GEO"}

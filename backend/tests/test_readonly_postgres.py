import os

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.db.session import SessionLocal

pytestmark = pytest.mark.skipif(
    not os.getenv("TEST_DATABASE_URL"),
    reason="TEST_DATABASE_URL is not configured",
)


def test_app_postgres_session_rejects_and_rolls_back_write():
    db = SessionLocal()
    try:
        try:
            db.execute(
                text(
                    "INSERT INTO satellites (norad_cat_id, object_name) "
                    "VALUES (-9223372036854775000, 'readonly-test')"
                )
            )
        except DBAPIError as exc:
            db.rollback()
            assert getattr(exc.orig, "sqlstate", None) == "25006"
        else:
            db.rollback()
            pytest.fail("The application PostgreSQL session accepted a write")
    finally:
        db.close()

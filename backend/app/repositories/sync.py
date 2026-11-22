from datetime import datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from ..models.satellite import Conjunction, GPHistory, Satellite


def latest_gp_fetched_at(db: Session) -> datetime | None:
    return db.scalar(select(func.max(GPHistory.fetched_at)))


def _insert(db: Session, model, values: dict[str, Any]):
    dialect = db.get_bind().dialect.name
    if dialect == "postgresql":
        return pg_insert(model).values(**values)
    if dialect == "sqlite":
        return sqlite_insert(model).values(**values)
    raise RuntimeError(f"Unsupported database dialect for upsert: {dialect}")


def upsert_satellite(db: Session, values: dict[str, Any]) -> None:
    statement = _insert(db, Satellite, values)
    update_values = {
        key: func.coalesce(getattr(statement.excluded, key), getattr(Satellite, key))
        for key in values
        if key not in {"norad_cat_id", "updated_at"}
    }
    update_values["updated_at"] = statement.excluded.updated_at
    db.execute(
        statement.on_conflict_do_update(
            index_elements=[Satellite.norad_cat_id],
            set_=update_values,
        )
    )


def upsert_gp_elements(db: Session, values: dict[str, Any]) -> None:
    statement = _insert(db, GPHistory, values)
    update_values = {
        key: getattr(statement.excluded, key)
        for key in values
        if key not in {"norad_cat_id", "epoch"}
    }
    db.execute(
        statement.on_conflict_do_update(
            index_elements=[GPHistory.norad_cat_id, GPHistory.epoch],
            set_=update_values,
        )
    )


def upsert_conjunction(db: Session, values: dict[str, Any]) -> None:
    statement = _insert(db, Conjunction, values)
    update_values = {
        key: getattr(statement.excluded, key)
        for key in values
        if key not in {"norad_cat_id_1", "norad_cat_id_2", "tca"}
    }
    db.execute(
        statement.on_conflict_do_update(
            index_elements=[
                Conjunction.norad_cat_id_1,
                Conjunction.norad_cat_id_2,
                Conjunction.tca,
            ],
            set_=update_values,
        )
    )


def commit_sync(db: Session) -> None:
    db.commit()

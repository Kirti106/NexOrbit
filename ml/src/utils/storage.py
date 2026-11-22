"""Database access and idempotent upserts.

All database access for the ML module is intentionally centralized here.
"""

from __future__ import annotations

import os
from collections.abc import Iterable, Mapping
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session


ML_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ML_ROOT / ".env")


def get_database_url() -> str:
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError(
            "DATABASE_URL is not set. Configure ml/.env; database credentials "
            "must never be hardcoded."
        )
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
        
    return url


def create_database_engine() -> Engine:
    return create_engine(get_database_url(), pool_pre_ping=True)


@contextmanager
def session_scope(engine: Engine | None = None):
    db_engine = engine or create_database_engine()
    session = Session(db_engine)
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def upsert_gp_history(session: Session, rows: Iterable[Mapping[str, Any]]) -> int:
    sql = text("""
        INSERT INTO gp_history (
            norad_cat_id, epoch, mean_motion, eccentricity, inclination,
            ra_of_asc_node, arg_of_pericenter, mean_anomaly, bstar,
            mean_motion_dot, mean_motion_ddot, element_set_no, rev_at_epoch,
            fetched_at
        ) VALUES (
            :norad_cat_id, :epoch, :mean_motion, :eccentricity, :inclination,
            :ra_of_asc_node, :arg_of_pericenter, :mean_anomaly, :bstar,
            :mean_motion_dot, :mean_motion_ddot, :element_set_no, :rev_at_epoch,
            :fetched_at
        )
        ON CONFLICT (norad_cat_id, epoch) DO UPDATE SET
            mean_motion = EXCLUDED.mean_motion,
            eccentricity = EXCLUDED.eccentricity,
            inclination = EXCLUDED.inclination,
            ra_of_asc_node = EXCLUDED.ra_of_asc_node,
            arg_of_pericenter = EXCLUDED.arg_of_pericenter,
            mean_anomaly = EXCLUDED.mean_anomaly,
            bstar = EXCLUDED.bstar,
            mean_motion_dot = EXCLUDED.mean_motion_dot,
            mean_motion_ddot = EXCLUDED.mean_motion_ddot,
            element_set_no = EXCLUDED.element_set_no,
            rev_at_epoch = EXCLUDED.rev_at_epoch,
            fetched_at = EXCLUDED.fetched_at
    """)
    changed = 0
    for row in rows:
        session.execute(sql, dict(row))
        changed += 1
    return changed


def upsert_conjunctions(session: Session, rows: Iterable[Mapping[str, Any]]) -> int:
    sql = text("""
        INSERT INTO conjunctions (
            norad_cat_id_1, norad_cat_id_2, object_name_1, object_name_2,
            tca, min_range_km, rel_speed_kms, max_prob, dse_1, dse_2,
            dilution, is_constellation_artifact, risk_weight, fetched_at
        ) VALUES (
            :norad_cat_id_1, :norad_cat_id_2, :object_name_1, :object_name_2,
            :tca, :min_range_km, :rel_speed_kms, :max_prob, :dse_1, :dse_2,
            :dilution, :is_constellation_artifact, :risk_weight, :fetched_at
        )
        ON CONFLICT (norad_cat_id_1, norad_cat_id_2, tca) DO UPDATE SET
            min_range_km = EXCLUDED.min_range_km,
            rel_speed_kms = EXCLUDED.rel_speed_kms,
            max_prob = EXCLUDED.max_prob,
            dse_1 = EXCLUDED.dse_1,
            dse_2 = EXCLUDED.dse_2,
            dilution = EXCLUDED.dilution,
            object_name_1 = EXCLUDED.object_name_1,
            object_name_2 = EXCLUDED.object_name_2,
            is_constellation_artifact = EXCLUDED.is_constellation_artifact,
            risk_weight = EXCLUDED.risk_weight,
            fetched_at = EXCLUDED.fetched_at
    """)
    changed = 0
    for row in rows:
        session.execute(sql, dict(row))
        changed += 1
    return changed


def insert_model_run(
    session: Session,
    *,
    task: str,
    model_name: str,
    version: str,
    params: Mapping[str, Any],
    metrics: Mapping[str, Any],
) -> int:
    result = session.execute(
        text("""
            INSERT INTO model_runs (task, model_name, version, params, metrics)
            VALUES (:task, :model_name, :version, CAST(:params AS JSONB),
                    CAST(:metrics AS JSONB))
            RETURNING id
        """),
        {
            "task": task,
            "model_name": model_name,
            "version": version,
            "params": __import__("json").dumps(params),
            "metrics": __import__("json").dumps(metrics),
        },
    )
    return int(result.scalar_one())


def upsert_satellites(session: Session, rows: Iterable[Mapping[str, Any]]) -> int:
    sql = text("""
        INSERT INTO satellites (
            norad_cat_id, object_name, object_id,
            object_type, owner_country, country, launch_date, decay_date,
            rcs_size, decay_status, source, updated_at
        ) VALUES (
            :norad_cat_id, :object_name, :object_id,
            :object_type, :owner_country, :owner_country, :launch_date, :decay_date,
            :rcs_size, :decay_status, 'CelesTrak-SATCAT', NOW()
        )
        ON CONFLICT (norad_cat_id) DO UPDATE SET
            object_name = EXCLUDED.object_name,
            object_id = EXCLUDED.object_id,
            object_type = EXCLUDED.object_type,
            country = EXCLUDED.country,
            owner_country = EXCLUDED.owner_country,
            launch_date = EXCLUDED.launch_date,
            decay_date = EXCLUDED.decay_date,
            rcs_size = EXCLUDED.rcs_size,
            decay_status = EXCLUDED.decay_status,
            source = EXCLUDED.source,
            updated_at = NOW()
    """)
    changed = 0
    for row in rows:
        session.execute(sql, dict(row))
        changed += 1
    return changed


def insert_prediction(
    session: Session,
    *,
    model_run_id: int,
    norad_cat_id: int | None,
    target_time: Any,
    output: Mapping[str, Any],
) -> int:
    import json

    result = session.execute(
        text("""
            INSERT INTO predictions (
                model_run_id, norad_cat_id, target_time, output
            ) VALUES (
                :model_run_id, :norad_cat_id, :target_time,
                CAST(:output AS JSONB)
            )
            RETURNING id
        """),
        {
            "model_run_id": model_run_id,
            "norad_cat_id": norad_cat_id,
            "target_time": target_time,
            "output": json.dumps(output),
        },
    )
    return int(result.scalar_one())

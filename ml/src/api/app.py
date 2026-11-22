from __future__ import annotations

import math
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Literal

import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sgp4.api import SatrecArray, jday

from ..propagation.sgp4 import (
    ground_track,
    propagate,
    satrec_from_database,
    satrec_from_gp,
    _satellite_for_skyfield,
)
from ..utils.storage import create_database_engine
from .models import (
    AnomalyListResponse,
    AnomalyResponse,
    ConjunctionListResponse,
    ConjunctionResponse,
    GroundTrackResponse,
    GroundTrackPoint,
    HealthResponse,
    LivePosition,
    LiveResponse,
    PositionResponse,
    SatelliteListResponse,
    SatelliteResponse,
    StatsResponse,
)

MODEL_VERSION = "2026-11-22-v1"
now = lambda: datetime.now(timezone.utc)

origins = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
    if origin.strip()
]

app = FastAPI(title="NexOrbit ML API", version=MODEL_VERSION)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)


def utc(value: datetime | str) -> datetime:
    parsed = value if isinstance(value, datetime) else datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


@app.get("/health", response_model=HealthResponse)
def health():
    try:
        engine = create_database_engine()
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        database = "connected"
        status: Literal["healthy", "degraded"] = "healthy"
    except Exception:
        database = "unavailable"
        status = "degraded"
    return HealthResponse(model_version=MODEL_VERSION, generated_at=now(), status=status, database=database)


@app.get("/satellites", response_model=SatelliteListResponse)
def satellites(
    type: str | None = None,
    q: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
):
    clauses = []
    params: dict = {"limit": limit}
    if type:
        clauses.append("LOWER(object_type) = LOWER(:type)")
        params["type"] = type
    if q:
        clauses.append("(CAST(norad_cat_id AS text) ILIKE :q OR object_name ILIKE :q)")
        params["q"] = f"%{q}%"
    where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
    engine = create_database_engine()
    with engine.connect() as connection:
        total = connection.execute(
            text(f"SELECT count(*) FROM satellites {where}"),
            params,
        ).scalar_one()
        rows = connection.execute(
            text(f"""
                SELECT norad_cat_id, object_name, COALESCE(object_type,'UNKNOWN') AS object_type,
                       owner_country, launch_date, decay_date, rcs_size
                FROM satellites {where}
                ORDER BY object_name NULLS LAST, norad_cat_id
                LIMIT :limit
            """),
            params,
        ).mappings().all()
    items = [
        SatelliteResponse(
            model_version=MODEL_VERSION,
            generated_at=now(),
            norad_id=row["norad_cat_id"],
            name=row["object_name"] or "",
            object_type=row["object_type"],
            owner_country=row["owner_country"],
            launch_date=utc(row["launch_date"]) if row["launch_date"] else None,
            decay_date=utc(row["decay_date"]) if row["decay_date"] else None,
            rcs_size=row["rcs_size"],
        )
        for row in rows
    ]
    return SatelliteListResponse(model_version=MODEL_VERSION, generated_at=now(), total=int(total), items=items)


@app.get("/satellites/live", response_model=LiveResponse)
def satellites_live(limit: int = Query(default=500, ge=1, le=500)):
    engine = create_database_engine()
    timestamp = now()
    # Use SQLAlchemy to obtain the latest epoch for each requested satellite.
    with engine.connect() as connection:
        rows = connection.execute(
            text("""
                WITH latest AS (
                  SELECT gp.*, ROW_NUMBER() OVER (
                    PARTITION BY gp.norad_cat_id ORDER BY gp.epoch DESC
                  ) AS rn
                  FROM gp_history gp
                )
                SELECT l.norad_cat_id, s.object_name, COALESCE(s.object_type,'UNKNOWN') AS object_type,
                       l.epoch, l.mean_motion, l.eccentricity, l.inclination,
                       l.ra_of_asc_node, l.arg_of_pericenter, l.mean_anomaly,
                       l.bstar, l.mean_motion_dot,
                       COALESCE(l.mean_motion_ddot,0) AS mean_motion_ddot,
                       COALESCE(l.element_set_no,0) AS element_set_no,
                       COALESCE(l.rev_at_epoch,0) AS rev_at_epoch
                FROM latest l
                JOIN satellites s ON s.norad_cat_id=l.norad_cat_id
                WHERE l.rn=1
                LIMIT :limit
            """),
            {"limit": limit},
        ).mappings().all()

    satrecs = []
    names = []
    ids = []
    types = []
    for row in rows:
        try:
            record = {
                "NORAD_CAT_ID": row["norad_cat_id"],
                "EPOCH": row["epoch"],
                "MEAN_MOTION": row["mean_motion"],
                "ECCENTRICITY": row["eccentricity"],
                "INCLINATION": row["inclination"],
                "RA_OF_ASC_NODE": row["ra_of_asc_node"],
                "ARG_OF_PERICENTER": row["arg_of_pericenter"],
                "MEAN_ANOMALY": row["mean_anomaly"],
                "BSTAR": row["bstar"],
                "MEAN_MOTION_DOT": row["mean_motion_dot"],
                "MEAN_MOTION_DDOT": row["mean_motion_ddot"],
                "ELEMENT_SET_NO": row["element_set_no"],
                "REV_AT_EPOCH": row["rev_at_epoch"],
            }
            satrecs.append(satrec_from_gp(record))
            names.append(row["object_name"] or "")
            ids.append(row["norad_cat_id"])
            types.append(row["object_type"])
        except (LookupError, ValueError):
            continue
    if not satrecs:
        items = []
    else:
        jd, fr = jday(
            timestamp.year, timestamp.month, timestamp.day,
            timestamp.hour, timestamp.minute,
            timestamp.second + timestamp.microsecond / 1_000_000,
        )
        errors, positions, _ = SatrecArray(satrecs).sgp4(
            np.array([jd] * len(satrecs)),
            np.array([fr] * len(satrecs)),
        )
        items = []
        from skyfield.api import load as skyfield_load, wgs84
        sky_time = skyfield_load.timescale().from_datetime(timestamp)
        for index, satrec in enumerate(satrecs):
            if np.asarray(errors[index]).size and int(np.asarray(errors[index]).ravel()[0]) != 0:
                continue
            try:
                sky_satellite = _satellite_for_skyfield(satrec)
                subpoint = wgs84.subpoint(sky_satellite.at(sky_time))
            except ValueError:
                continue
            items.append(
                LivePosition(
                    norad_id=ids[index],
                    name=names[index],
                    object_type=types[index],
                    latitude=float(subpoint.latitude.degrees),
                    longitude=float(subpoint.longitude.degrees),
                    altitude_km=float(subpoint.elevation.km),
                )
            )
    return LiveResponse(
        model_version=MODEL_VERSION,
        generated_at=timestamp,
        frame="TEME position converted to geodetic",
        items=items,
    )


@app.get("/satellites/{norad_id}/position", response_model=PositionResponse)
def satellite_position(norad_id: int, time: str | None = None):
    if norad_id <= 0:
        raise HTTPException(status_code=422, detail="norad_id must be positive")
    timestamp = utc(time) if time else now()
    try:
        result = propagate(norad_id, [timestamp])[0]
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="Satellite not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    satrec = satrec_from_database(norad_id)
    speed = math.sqrt(sum(float(value) ** 2 for value in result["velocity"].values()))
    altitude_km = None
    try:
        sky_satellite = _satellite_for_skyfield(satrec)
        from skyfield.api import load as skyfield_load, wgs84
        subpoint = wgs84.subpoint(sky_satellite.at(skyfield_load.timescale().from_datetime(timestamp)))
        altitude_km = float(subpoint.elevation.km)
    except ValueError:
        altitude_km = None
    with create_database_engine().connect() as connection:
        name = connection.execute(
            text("SELECT object_name FROM satellites WHERE norad_cat_id=:id"),
            {"id": norad_id},
        ).scalar()
    if name is None:
        raise HTTPException(status_code=404, detail="Satellite not found")
    return PositionResponse(
        model_version=MODEL_VERSION,
        generated_at=now(),
        norad_id=norad_id,
        name=name,
        timestamp=timestamp,
        frame="TEME",
        position=result["position"],
        velocity=result["velocity"],
        altitude_km=altitude_km,
        speed_kms=speed,
    )


@app.get("/satellites/{norad_id}/ground-track", response_model=GroundTrackResponse)
def satellite_ground_track(
    norad_id: int,
    hours: float = Query(default=3, ge=0.25, le=24),
    step_s: int = Query(default=60, ge=10, le=3600),
):
    if norad_id <= 0:
        raise HTTPException(status_code=422, detail="norad_id must be positive")
    try:
        start = now()
        track = ground_track(norad_id, start, start + timedelta(hours=hours), timedelta(seconds=step_s))
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="Satellite not found") from exc
    points = [GroundTrackPoint(**point) for point in track]
    return GroundTrackResponse(model_version=MODEL_VERSION, generated_at=now(), norad_id=norad_id, points=points)


def derive_tier(row) -> str:
    probability = float(row["max_prob"] or 0)
    if row["is_constellation_artifact"]:
        return "low"
    if probability >= 1e-3 or (probability >= 1e-5 and float(row["min_range_km"] or 999) <= 50):
        return "high"
    if probability >= 1e-5:
        return "medium"
    return "low"


TIER_SQL = """
CASE
  WHEN is_constellation_artifact THEN 'low'
  WHEN COALESCE(max_prob,0) >= 1e-3
    OR (COALESCE(max_prob,0) >= 1e-5 AND COALESCE(min_range_km,999) <= 50) THEN 'high'
  WHEN COALESCE(max_prob,0) >= 1e-5 THEN 'medium'
  ELSE 'low'
END
"""  # mirrors derive_tier() so filtering/counting can happen in SQL


@app.get("/conjunctions", response_model=ConjunctionListResponse)
def conjunctions(
    risk: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    min_tca: str | None = None,
    include_artifacts: bool = False,
):
    clauses = []
    params: dict = {"limit": limit}
    if not include_artifacts:
        clauses.append("is_constellation_artifact=false")
    if min_tca:
        try:
            parsed = utc(min_tca)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail="min_tca must be an ISO UTC timestamp") from exc
        clauses.append("tca >= :min_tca")
        params["min_tca"] = parsed
    if risk:
        if risk.lower() not in {"low", "medium", "high"}:
            raise HTTPException(status_code=422, detail="risk must be low, medium, or high")
        clauses.append(f"({TIER_SQL}) = :risk")
        params["risk"] = risk.lower()
    where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
    with create_database_engine().connect() as connection:
        rows = connection.execute(
            text(f"""
                SELECT norad_cat_id_1, norad_cat_id_2, object_name_1, object_name_2,
                       tca, min_range_km, rel_speed_kms, max_prob,
                       is_constellation_artifact, fetched_at
                FROM conjunctions
                {where}
                ORDER BY tca, min_range_km
                LIMIT :limit
            """),
            params,
        ).mappings().all()
    items = []
    for row in rows:
        tier = derive_tier(row)
        if risk and tier != risk.lower():
            continue
        items.append(ConjunctionResponse(
            norad_id_1=row["norad_cat_id_1"],
            norad_id_2=row["norad_cat_id_2"],
            object_name_1=row["object_name_1"],
            object_name_2=row["object_name_2"],
            tca=utc(row["tca"]),
            min_range_km=float(row["min_range_km"]),
            rel_speed_kms=float(row["rel_speed_kms"]) if row["rel_speed_kms"] is not None else None,
            max_prob=float(row["max_prob"]) if row["max_prob"] is not None else None,
            risk_tier=tier,
            is_artifact=bool(row["is_constellation_artifact"]),
            fetched_at=utc(row["fetched_at"]),
        ))
    return ConjunctionListResponse(
        model_version=MODEL_VERSION,
        generated_at=now(),
        basis="SOCRATES-derived, predicted, not observed",
        items=items,
    )


@app.get("/stats", response_model=StatsResponse)
def stats():
    with create_database_engine().connect() as connection:
        type_rows = connection.execute(
            text("""
                SELECT COALESCE(object_type,'UNKNOWN') AS object_type, count(*) AS count
                FROM satellites GROUP BY COALESCE(object_type,'UNKNOWN')
                ORDER BY count DESC
            """)
        ).mappings().all()
        total = sum(int(row["count"]) for row in type_rows)
        debris = sum(int(row["count"]) for row in type_rows if str(row["object_type"]).upper() in {"DEBRIS","DEB"})
        conjunction_count = int(connection.execute(text("SELECT count(*) FROM conjunctions")).scalar_one())
        gp_fresh = connection.execute(text("SELECT max(fetched_at) FROM gp_history")).scalar()
        socrates_fresh = connection.execute(text("SELECT max(fetched_at) FROM conjunctions")).scalar()
        high_risk = int(connection.execute(
            text(f"SELECT count(*) FROM conjunctions WHERE ({TIER_SQL}) = 'high'")
        ).scalar_one())
    return StatsResponse(
        model_version=MODEL_VERSION,
        generated_at=now(),
        satellites_by_object_type={row["object_type"]: int(row["count"]) for row in type_rows},
        tracked_satellites=total,
        high_risk_conjunctions=high_risk,
        conjunctions=conjunction_count,
        debris_share=float(debris / total) if total else 0.0,
        gp_freshest_at=utc(gp_fresh) if gp_fresh else None,
        socrates_fetched_at=utc(socrates_fresh) if socrates_fresh else None,
    )


@app.get("/anomalies", response_model=AnomalyListResponse)
def anomalies(limit: int = Query(default=100, ge=1, le=500)):
    with create_database_engine().connect() as connection:
        rows = connection.execute(
            text("""
                WITH latest AS (
                  SELECT gp.*, s.object_name,
                         ROW_NUMBER() OVER (PARTITION BY gp.norad_cat_id ORDER BY gp.epoch DESC) rn
                  FROM gp_history gp JOIN satellites s ON s.norad_cat_id=gp.norad_cat_id
                )
                SELECT * FROM latest WHERE rn=1
            """)
        ).mappings().all()
    if not rows:
        frame = pd.DataFrame()
        return AnomalyListResponse(model_version=MODEL_VERSION, generated_at=now(), basis="cross-sectional element profile, not maneuver detection", items=[])
    frame = pd.DataFrame(rows)
    features = ["mean_motion", "eccentricity", "inclination", "bstar"]
    available = [feature for feature in features if feature in frame]
    z_matrix = np.zeros((len(frame), len(available)))
    for index, feature in enumerate(available):
        values = pd.to_numeric(frame[feature], errors="coerce").fillna(0)
        median = values.median()
        mad = (values - median).abs().median()
        z = np.abs((values - median) / (1.4826 * mad)) if mad and mad > 0 else pd.Series(0, index=frame.index)
        z_matrix[:, index] = z.to_numpy()
    frame["score"] = z_matrix.sum(axis=1) / max(len(available), 1)
    frame["top_feature"] = [
        available[int(index)] if available else "unknown"
        for index in np.argmax(z_matrix, axis=1)
    ] if available else ["unknown"] * len(frame)
    frame = frame.sort_values("score", ascending=False).head(limit)
    items = [
        AnomalyResponse(
            norad_id=int(row["norad_cat_id"]),
            name=row["object_name"] or "",
            score=float(row["score"]),
            top_feature=row["top_feature"],
            label="unusual orbit profile",
        )
        for _, row in frame.iterrows()
    ]
    return AnomalyListResponse(
        model_version=MODEL_VERSION,
        generated_at=now(),
        basis="cross-sectional element profile, not maneuver detection",
        items=items,
    )

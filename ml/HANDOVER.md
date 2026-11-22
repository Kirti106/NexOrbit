# NexOrbit ML Handover

## 1. What was built

The ML module provides local CelesTrak GP/SATCAT/SOCRATES ingestion, SGP4
propagation, cross-sectional anomaly output, SOCRATES-derived conjunction
tiers, sustainability code, PostgreSQL migrations, and a FastAPI service on
port 8001.

## 2. Quick start

From a fresh clone:

```powershell
cd NexOrbit
Copy-Item .env.example .env
docker compose up --build -d

Set-Location frontend
npm install
npm run dev
```

Compose applies the database migrations and loads the checked-in sample
datasets when the database is empty. The integrated frontend is served at
`http://localhost:5173`, the backend at `http://localhost:8000`, and this ML API
at `http://localhost:8001`. The frontend calls the backend through Vite's
`/api` proxy; the backend proxies propagation requests to the ML API.

## 3. API contract

OpenAPI types: [openapi.json](openapi.json).

| Endpoint | Parameters | Purpose |
|---|---|---|
| `GET /health` | none | API/database health |
| `GET /satellites` | `type`, `q`, `limit` | Catalog search |
| `GET /satellites/live` | `limit=500` | Current geodetic positions |
| `GET /satellites/{norad_id}/position` | `time` | TEME position/velocity |
| `GET /satellites/{norad_id}/ground-track` | `hours=3`, `step_s=60` | Ground-track points |
| `GET /conjunctions` | `risk`, `limit`, `min_tca`, `include_artifacts=false` | Ranked SOCRATES events |
| `GET /stats` | none | Counts/freshness |
| `GET /anomalies` | `limit` | Cross-sectional unusual orbit profiles |

Actual health response:

```json
{"model_version":"2026-11-22-v1","generated_at":"2026-11-21T22:21:39.533311Z","status":"healthy","database":"connected"}
```

Actual stats response:

```json
{"model_version":"2026-11-22-v1","generated_at":"2026-11-21T22:21:48.130000Z","satellites_by_object_type":{"PAYLOAD":17494,"UNKNOWN":2682,"ROCKET BODY":4},"tracked_satellites":20180,"high_risk_conjunctions":73868,"conjunctions":189379,"debris_share":0.0,"gp_freshest_at":"2026-11-21T22:00:30.740362Z","socrates_fetched_at":"2026-11-21T22:00:47.414106Z"}
```

Actual ISS position shape:

```json
{"model_version":"2026-11-22-v1","generated_at":"2026-11-21T22:23:40.973787Z","norad_id":25544,"name":"ISS (ZARYA)","timestamp":"2026-11-21T22:23:40.493424Z","frame":"TEME","position":{"x":4541.878270576898,"y":-160.9150373297332,"z":5040.509306929819},"velocity":{"x":2.3877192891598873,"y":7.028720989867507,"z":-1.9160933895888037},"altitude_km":420.5296078443279,"speed_kms":7.666520464647321}
```

Actual conjunction response shape:

```json
{"model_version":"2026-11-22-v1","generated_at":"2026-11-21T22:22:10.861600Z","basis":"SOCRATES-derived, predicted, not observed","items":[{"norad_id_1":64084,"norad_id_2":68633,"object_name_1":"STARLINK-34157 [+]","object_name_2":"MISR-C-2 [+]","tca":"2026-11-20T20:00:02.449000Z","min_range_km":2.605,"rel_speed_kms":9.21,"max_prob":0.00001618,"risk_tier":"high","is_artifact":false,"fetched_at":"2026-11-21T22:00:47.414106Z"}]}
```

## 4. Database

Verified row counts:

- `satellites`: 17,498 catalog objects plus 2682 GP/debris/unknown stubs = 20,180
- `gp_history`: 19,611
- `conjunctions`: 189,379
- Constellation artifacts: 3,701

Restore a prepared dump on a fresh machine:

```powershell
.\ml\scripts\restore_db.ps1 -DumpFile .\nexorbit.dump
```

Create a portable dump:

```powershell
.\ml\scripts\dump_db.ps1
```

Rebuild without an existing dump:

```powershell
.\ml\scripts\load_samples.ps1
```

## 5. Environment variables

| Name | Purpose | Example |
|---|---|---|
| `DATABASE_URL` | Host-side SQLAlchemy PostgreSQL URL | `postgresql+psycopg2://root:fake_password@127.0.0.1:5432/nexorbit` |
| `CORS_ORIGINS` | Comma-separated frontend origins | `http://localhost:5173` |
| `POSTGRES_DB` | Compose database name | `nexorbit` |
| `POSTGRES_USER` | Compose database role | `nexorbit` |
| `POSTGRES_PASSWORD` | Compose database password | `change_me` |
| `ML_API_URL` | Backend-to-ML service URL | `http://ml_api:8001` |

## 6. Data semantics

GP mean elements are propagation inputs and stale within days. SOCRATES rows
are predicted close approaches, not observed collisions. `MAX_PROB` is a
SOCRATES maximum-probability estimate, not a real collision probability.
Conjunction output exposes `risk_tier` first and `max_prob` only as secondary
data.

An event is down-weighted and flagged `is_artifact` when range is <=1 km and
both object names normalize to the same constellation base. There are 3,701
such rows and they receive a 0.1 risk weight. It is not deleted.

Anomaly output is a cross-sectional `unusual orbit profile` score. The
database has one GP epoch per object for this handover, so it does not detect
or claim maneuvers.

All timestamps are timezone-aware UTC.

## 7. Frontend display guidance

Display `risk_tier` as the primary label and put `max_prob` in a tooltip.
Display SOCRATES events as predictions and label them with `predictions as of
<fetched_at>`. Do not describe them as observed collisions.

## 8. Known issues and next steps

Priority:

1. Add a second GP snapshot at least two hours later to enable the residual
   anomaly detector.
2. Schedule GP at >=2-hour intervals and SOCRATES daily.
3. Expose clustering and object classification endpoints.
4. Expose sustainability forecast/scenario endpoints.
5. Replace remaining stubs for Bhoonidhi, VEDAS, and Bhuvan after authentication,
   endpoints, formats, and catalog availability are confirmed.

## 9. Troubleshooting

- Port 5432 conflict: stop the conflicting local PostgreSQL or change the host
  publication.
- Role does not exist/old volume: `docker compose down -v`, then
  `docker compose up --build -d` and reapply migrations/load or restore.
- CelesTrak rate limits: use local sample or raw cache; live requests must retry
  and respect the >=2-hour GP cache.
- OneDrive paths: keep PowerShell paths and scripts in quotes and run from the
  repository root.

## Pipeline commands

Live ingest GP:

```powershell
cd ml
python -m src.pipeline --source gp --group active
```

Ingest from local files:

```powershell
python -m src.pipeline --source gp --from-file ml/data/samples/celestrak_gp_active.json
python -m src.pipeline --source satcat --from-file ml/data/samples/celestrak_satcat_active.json
python -m src.pipeline --source socrates --from-file ml/data/samples/socrates_sample.csv
```

SOCRATES live refresh is deliberately not configured until a verified direct
CSV endpoint is available. Refresh from file:

```powershell
python -m src.pipeline --conjunctions-refresh --from-file ml/data/samples/socrates_sample.csv
```

Recompute cross-sectional anomalies:

```powershell
python -m src.pipeline --anomalies-recompute
```

Recommended cron schedule: GP every 2 hours; SOCRATES once daily.

Clustering, classification, forecast, residual anomaly detector, and ISRO
adapters remain code/not exposed via API yet. ISRO adapters are stubs because
auth/API/formats are unknown.

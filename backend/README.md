# NexOrbit backend API

The backend is the frontend-facing FastAPI service on port `8000`. It reads
only the existing `satellites`, `gp_history`, and `conjunctions` tables in
PostgreSQL. Propagation, live positions, and anomaly scoring are delegated to
the separate ML service on port `8001`.

The application does not create or migrate database objects. PostgreSQL
connections use `default_transaction_read_only=on` and a 10-second statement
timeout. Provision the existing schema outside this service before running it.
SQLite is used only by the local API test fixture.

## Run locally

From `backend/`, install the pinned requirements, set `DATABASE_URL` and
`ML_API_URL`, then run:

```powershell
python -m pip install -r requirements.txt
$env:DATABASE_URL = "postgresql+psycopg://user:password@localhost:5432/nexorbit"
$env:ML_API_URL = "http://localhost:8001"
uvicorn app.main:app --reload
```

Do not run schema migrations from the backend. Swagger UI is available at
`http://localhost:8000/docs`; readiness checks verify that the three required
tables are present.

## API (`/api/v1`)

| Method | Path | Purpose |
|---|---|---|
| GET | `/satellites` | Search/filter catalog and latest GP-derived orbit data |
| GET | `/satellites/{norad_id}` | Catalog, latest elements, and launch/status information |
| GET | `/satellites/{norad_id}/history` | Recent GP element sets, newest first |
| GET | `/satellites/{norad_id}/conjunctions` | Paged past and upcoming predicted conjunctions |
| GET | `/satellites/{norad_id}/position` | Position and velocity at a UTC time |
| GET | `/satellites/{norad_id}/ground-track` | Predicted ground-track samples |
| GET | `/satellites/live` | Cached current geodetic positions |
| GET | `/conjunctions` | Filter and page predicted conjunctions |
| GET | `/conjunctions/summary` | Counts by risk tier and derived severity, all and next 7 days |
| GET | `/conjunctions/export?format=csv\|json` | Stream a filtered export, capped at 5,000 rows |
| GET | `/conjunctions/{id}` | Predicted conjunction detail |
| GET | `/alerts` | Compatibility alias for the conjunction listing |
| GET | `/stats` | Catalog totals and data freshness |
| GET | `/analytics?period=30D` | Aggregates for `7D`, `30D`, `90D`, or `1Y` |
| GET | `/meta` | API version, data freshness, and data-basis notes |
| GET | `/anomalies` | ML unusual-orbit profiles (not maneuver detections) |
| GET | `/health` | Backend, database, and ML health |
| GET | `/ready` | Database connectivity and required-table readiness |
| POST | `/admin/sync/gp` | Retained compatibility path; read-only DB sessions cannot persist syncs |
| POST | `/admin/sync/conjunctions` | Retained compatibility path; read-only DB sessions cannot persist syncs |

Conjunction responses use `risk_tier` as the primary classification;
`severity` is derived from separation distance because the existing schema has
no severity column (`critical` ≤ 1 km, `high` ≤ 10 km, `medium` ≤ 50 km,
`low` > 50 km, and `unknown` when distance is unavailable). Admin paths require
`X-API-Key`, are rate-limited, and cannot write through the read-only
PostgreSQL connection.

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `postgresql+psycopg://localhost/nexorbit` | PostgreSQL connection URL |
| `CORS_ORIGINS` | `http://localhost:5173` | Comma-separated allowed origins |
| `ML_API_URL` | `http://localhost:8001` | Separate ML service base URL |
| `ADMIN_API_KEY` | Empty | Key required by retained admin paths; configure a secret outside source control |
| `CACHE_TTL` | `10` | Cache lifetime in seconds for aggregate and live responses |
| `RATE_LIMIT_PER_MINUTE` | `120` | Per-client-IP in-memory request limit |
| `LOG_JSON` | `false` | Emit structured JSON logs when `true` |
| `TEST_DATABASE_URL` | Unset | Optional real PostgreSQL URL for read-only integration tests |
| `SCHEDULER_ENABLED` | `false` | Existing optional scheduler switch; database writes remain blocked |
| `SOCRATES_URL` | Unset | Optional configured SOCRATES source URL |

The service also caps request `limit` at 5,000 and `offset` at 100,000. Individual
endpoints may impose lower limits. Cacheable GETs return `ETag` and
`Cache-Control`; matching `If-None-Match` requests receive `304 Not Modified`.
Errors use `{"error": {"code": "...", "message": "..."}}`.

## Tests and lint

From `backend/`:

```powershell
python -m pytest -q
python -m ruff check app tests
```

The ordinary endpoint suite uses an isolated SQLite fixture. PostgreSQL
integration tests and the read-only write-rejection check are skipped unless
`TEST_DATABASE_URL` points to a PostgreSQL database that already contains the
three required tables. Those integration tests issue SELECTs in a transaction
that is rolled back; the write-rejection check attempts one write and verifies
PostgreSQL rejects it with read-only SQLSTATE `25006`.

## Data rules

- SOCRATES conjunctions are predictions, not observed collisions.
- `max_prob` is never described as a real collision probability.
- Anomalies are unusual orbit profiles, not maneuver detections.
- Orbit class is an approximate derivation from orbital elements.
- Timestamps are UTC.
- Empty or unavailable aggregates are not fabricated; unavailable values
  include a reason.

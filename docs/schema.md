# Shared NexOrbit database schema

`datasets/init.sql` and the backend Alembic revision
`backend/alembic/versions/001_unified_schema.py` define one PostgreSQL/PostGIS
schema for the catalog and ML service. The backend applies Alembic before
starting; the SQL file initializes a fresh Compose volume so the separate ML
service can use the same tables.

## Tables

| Table | Purpose | Important keys |
|---|---|---|
| `satellites` | SATCAT metadata and optional TLE text | `norad_cat_id` unique; indexed `object_name` |
| `gp_history` | Timestamped GP orbital elements | unique `(norad_cat_id, epoch)` |
| `conjunctions` | SOCRATES-derived predicted close approaches | unique `(norad_cat_id_1, norad_cat_id_2, tca)` |
| `model_runs` | ML model execution metadata | `id` |
| `predictions` | Model output records | `id`, optional `model_run_id` |

`GPHistory` is the authoritative source for orbital elements. The catalog is
shared with ML using `norad_cat_id` and `object_name`; backend ORM aliases
`norad_id` and `name` map to those same columns and do not create duplicate
identifiers. The initial prototype's separate `orbital_elements`,
`orbital_positions`, and `conjunction_events` tables are not used by the
unified API.

## Conjunction semantics

Conjunctions are predictions, not observed collisions. `max_prob` is retained
as the supplied SOCRATES secondary value and must not be described as a real
collision probability. `risk_tier` is a backend-derived label, and
constellation artifacts are retained but marked separately.

All time columns are `TIMESTAMPTZ` and API times are UTC-aware. PostgreSQL
indexes support NORAD lookup, satellite-name search, GP epoch lookup,
conjunction TCA, and conjunction risk-tier filtering.

## Existing volumes

Alembic revision `001_unified_schema` is idempotent for fresh schema objects
and adds/backfills the shared catalog columns from the original `norad_id` and
`name` columns in existing volumes. Back up production data before applying
schema revisions.

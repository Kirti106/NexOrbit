# NexOrbit ML Module

The ML module is self-contained under `ml/`. It uses `DATABASE_URL` from
`ml/.env` only and never hardcodes credentials.

## Database

Run `ml/db/migrations/001_create_ml_tables.sql`, then
`ml/db/migrations/002_compat_satellites_catalog.sql` against PostgreSQL.

The 002 migration preserves the backend's existing `satellites.norad_id`,
TLE, and ORM columns while adding SATCAT metadata. The current backend's
`satellites` primary-key and the planned `norad_cat_id` primary-key design
are therefore compatibility-related, not identical. GP and conjunction
historical tables use NORAD IDs but do not add a hard foreign key to the
backend table until that schema mismatch is resolved explicitly.

All database access lives in `src/utils/storage.py`.

## Data semantics

- GP mean elements are for SGP4 propagation; they are not precise state vectors.
- SOCRATES rows are predictions of close approaches, not observed collisions.
- SOCRATES `MAX_PROB` is a maximum-probability estimate under assumed covariance.
- Conjunction outputs are SOCRATES-derived risk tiers, never actual collision
  probabilities.
- SOCRATES rows whose range is at most 1 km and whose object names share the
  same constellation base are flagged as `is_constellation_artifact` and receive
  a 0.1 risk weight. This does not remove the row or alter the stored
  `MAX_PROB`; it prevents same-constellation element artifacts from being
  ranked as high-risk events.
- Anomaly flags identify anomalous element changes, not confirmed maneuvers.
- Time-based splits are used for temporal ML tasks.

## Leakage

For conjunction classification, `MAX_PROB` is used only to derive the label.
It is excluded from model features.

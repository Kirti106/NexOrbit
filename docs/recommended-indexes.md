# Recommended indexes for review

These are suggestions only. The backend does not create or execute indexes.
Review the live schema and query plans before applying any of them yourself.

```sql
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_gp_history_norad_epoch_desc
    ON gp_history (norad_cat_id, epoch DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_conjunctions_norad_1_tca
    ON conjunctions (norad_cat_id_1, tca);

CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_conjunctions_norad_2_tca
    ON conjunctions (norad_cat_id_2, tca);

CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_gp_history_fetched_at
    ON gp_history (fetched_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_conjunctions_fetched_at
    ON conjunctions (fetched_at DESC);
```

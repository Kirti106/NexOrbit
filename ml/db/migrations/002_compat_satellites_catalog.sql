-- Compatibility migration for the existing FastAPI satellite table.
-- It preserves norad_id and TLE columns used by the backend while adding
-- the SATCAT metadata required by the ML module.
ALTER TABLE satellites ADD COLUMN IF NOT EXISTS norad_cat_id BIGINT;
ALTER TABLE satellites ADD COLUMN IF NOT EXISTS object_name VARCHAR(255);
ALTER TABLE satellites ADD COLUMN IF NOT EXISTS object_id VARCHAR(100);
ALTER TABLE satellites ADD COLUMN IF NOT EXISTS owner_country VARCHAR(100);
ALTER TABLE satellites ADD COLUMN IF NOT EXISTS launch_date TIMESTAMPTZ;
ALTER TABLE satellites ADD COLUMN IF NOT EXISTS decay_date TIMESTAMPTZ;
ALTER TABLE satellites ADD COLUMN IF NOT EXISTS rcs_size VARCHAR(50);
ALTER TABLE satellites ADD COLUMN IF NOT EXISTS decay_status VARCHAR(50);
ALTER TABLE satellites ADD COLUMN IF NOT EXISTS country VARCHAR(100);
ALTER TABLE satellites ADD COLUMN IF NOT EXISTS line1 VARCHAR(100);
ALTER TABLE satellites ADD COLUMN IF NOT EXISTS line2 VARCHAR(100);
ALTER TABLE satellites ADD COLUMN IF NOT EXISTS epoch VARCHAR(32);
ALTER TABLE satellites ADD COLUMN IF NOT EXISTS source VARCHAR(80);
ALTER TABLE satellites ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW();

CREATE UNIQUE INDEX IF NOT EXISTS uq_satellites_norad_cat_id
    ON satellites(norad_cat_id);

CREATE TABLE IF NOT EXISTS satellites (
    norad_cat_id BIGINT PRIMARY KEY,
    object_name VARCHAR(255),
    object_id VARCHAR(100),
    object_type VARCHAR(50),
    country VARCHAR(100),
    owner_country VARCHAR(100),
    launch_date DATE,
    decay_date DATE,
    rcs_size VARCHAR(50),
    decay_status VARCHAR(50),
    line1 VARCHAR(100),
    line2 VARCHAR(100),
    epoch VARCHAR(32),
    source VARCHAR(80),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_satellites_object_name
    ON satellites(object_name);

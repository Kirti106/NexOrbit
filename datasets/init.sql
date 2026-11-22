CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE IF NOT EXISTS satellites (
    id BIGSERIAL PRIMARY KEY,
    norad_cat_id BIGINT NOT NULL,
    object_name VARCHAR(255) NOT NULL,
    object_id VARCHAR(100),
    object_type VARCHAR(50),
    owner_country VARCHAR(100),
    country VARCHAR(100),
    status VARCHAR(50),
    launch_date TIMESTAMPTZ,
    decay_date TIMESTAMPTZ,
    rcs_size VARCHAR(50),
    decay_status VARCHAR(50),
    line1 VARCHAR(100),
    line2 VARCHAR(100),
    epoch TIMESTAMPTZ,
    source VARCHAR(80),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS gp_history (
    id BIGSERIAL PRIMARY KEY,
    norad_cat_id BIGINT NOT NULL,
    epoch TIMESTAMPTZ NOT NULL,
    mean_motion DOUBLE PRECISION,
    eccentricity DOUBLE PRECISION,
    inclination DOUBLE PRECISION,
    ra_of_asc_node DOUBLE PRECISION,
    arg_of_pericenter DOUBLE PRECISION,
    mean_anomaly DOUBLE PRECISION,
    bstar DOUBLE PRECISION,
    mean_motion_dot DOUBLE PRECISION,
    mean_motion_ddot DOUBLE PRECISION,
    element_set_no INTEGER,
    rev_at_epoch INTEGER,
    fetched_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_gp_norad_epoch UNIQUE (norad_cat_id, epoch)
);

CREATE TABLE IF NOT EXISTS conjunctions (
    id BIGSERIAL PRIMARY KEY,
    norad_cat_id_1 BIGINT NOT NULL,
    norad_cat_id_2 BIGINT NOT NULL,
    object_name_1 VARCHAR(255),
    object_name_2 VARCHAR(255),
    tca TIMESTAMPTZ NOT NULL,
    min_range_km DOUBLE PRECISION,
    rel_speed_kms DOUBLE PRECISION,
    max_prob DOUBLE PRECISION,
    dse_1 DOUBLE PRECISION,
    dse_2 DOUBLE PRECISION,
    dilution DOUBLE PRECISION,
    is_constellation_artifact BOOLEAN NOT NULL DEFAULT FALSE,
    risk_weight DOUBLE PRECISION NOT NULL DEFAULT 1.0,
    risk_tier VARCHAR(10),
    fetched_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_conjunction_pair_tca UNIQUE (norad_cat_id_1, norad_cat_id_2, tca)
);

CREATE TABLE IF NOT EXISTS model_runs (
    id BIGSERIAL PRIMARY KEY,
    task VARCHAR(100) NOT NULL,
    model_name VARCHAR(100) NOT NULL,
    version VARCHAR(100) NOT NULL,
    params JSONB,
    metrics JSONB,
    trained_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS predictions (
    id BIGSERIAL PRIMARY KEY,
    model_run_id BIGINT REFERENCES model_runs(id),
    norad_cat_id BIGINT,
    target_time TIMESTAMPTZ,
    output JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_satellites_norad_cat_id ON satellites (norad_cat_id);
CREATE INDEX IF NOT EXISTS ix_satellites_object_name ON satellites (object_name);
CREATE INDEX IF NOT EXISTS ix_gp_history_norad_epoch ON gp_history (norad_cat_id, epoch DESC);
CREATE INDEX IF NOT EXISTS ix_conjunctions_tca ON conjunctions (tca);
CREATE INDEX IF NOT EXISTS ix_conjunctions_risk_tier ON conjunctions (risk_tier);
CREATE INDEX IF NOT EXISTS ix_predictions_target_time ON predictions (target_time);

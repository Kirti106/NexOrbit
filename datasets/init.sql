
-- Enable PostGIS
CREATE EXTENSION IF NOT EXISTS postgis;

-- Satellite catalogue
CREATE TABLE IF NOT EXISTS satellites (
    id BIGSERIAL PRIMARY KEY,
    norad_id BIGINT UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    object_type VARCHAR(50),
    country VARCHAR(100),
    status VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Orbital elements history
CREATE TABLE IF NOT EXISTS orbital_elements (
    id BIGSERIAL PRIMARY KEY,
    satellite_id BIGINT REFERENCES satellites(id),
    epoch TIMESTAMPTZ NOT NULL,
    inclination DOUBLE PRECISION,
    eccentricity DOUBLE PRECISION,
    mean_motion DOUBLE PRECISION,
    source VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Satellite positions
CREATE TABLE IF NOT EXISTS orbital_positions (
    id BIGSERIAL PRIMARY KEY,
    satellite_id BIGINT REFERENCES satellites(id),
    recorded_at TIMESTAMPTZ NOT NULL,
    x DOUBLE PRECISION NOT NULL,
    y DOUBLE PRECISION NOT NULL,
    z DOUBLE PRECISION NOT NULL,
    vx DOUBLE PRECISION,
    vy DOUBLE PRECISION,
    vz DOUBLE PRECISION,
    reference_frame VARCHAR(50) DEFAULT 'TEME'
);

-- Conjunction events
CREATE TABLE IF NOT EXISTS conjunction_events (
    id BIGSERIAL PRIMARY KEY,
    object_1_id BIGINT REFERENCES satellites(id),
    object_2_id BIGINT REFERENCES satellites(id),
    tca TIMESTAMPTZ NOT NULL,
    miss_distance_km DOUBLE PRECISION,
    relative_velocity_km_s DOUBLE PRECISION,
    collision_probability DOUBLE PRECISION,
    source VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_orbital_epoch
ON orbital_elements(epoch);

CREATE INDEX IF NOT EXISTS idx_positions_recorded_at
ON orbital_positions(recorded_at);

CREATE INDEX IF NOT EXISTS idx_conjunction_tca
ON conjunction_events(tca);

"""Create the shared catalog, GP, and SOCRATES tables."""

from alembic import op

revision = "001_unified_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS satellites (
            id BIGSERIAL PRIMARY KEY,
            norad_cat_id BIGINT,
            object_name VARCHAR(255),
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
        )
        """
    )
    op.execute(
        """
        ALTER TABLE satellites
          ADD COLUMN IF NOT EXISTS norad_cat_id BIGINT,
          ADD COLUMN IF NOT EXISTS object_name VARCHAR(255),
          ADD COLUMN IF NOT EXISTS object_id VARCHAR(100),
          ADD COLUMN IF NOT EXISTS object_type VARCHAR(50),
          ADD COLUMN IF NOT EXISTS owner_country VARCHAR(100),
          ADD COLUMN IF NOT EXISTS country VARCHAR(100),
          ADD COLUMN IF NOT EXISTS status VARCHAR(50),
          ADD COLUMN IF NOT EXISTS launch_date TIMESTAMPTZ,
          ADD COLUMN IF NOT EXISTS decay_date TIMESTAMPTZ,
          ADD COLUMN IF NOT EXISTS rcs_size VARCHAR(50),
          ADD COLUMN IF NOT EXISTS decay_status VARCHAR(50),
          ADD COLUMN IF NOT EXISTS line1 VARCHAR(100),
          ADD COLUMN IF NOT EXISTS line2 VARCHAR(100),
          ADD COLUMN IF NOT EXISTS epoch TIMESTAMPTZ,
          ADD COLUMN IF NOT EXISTS source VARCHAR(80),
          ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW()
        """
    )
    op.execute(
        """
        DO $$ BEGIN
          IF EXISTS (SELECT 1 FROM information_schema.columns
                     WHERE table_name='satellites' AND column_name='norad_id') THEN
            EXECUTE 'UPDATE satellites SET norad_cat_id = norad_id WHERE norad_cat_id IS NULL';
            EXECUTE 'ALTER TABLE satellites ALTER COLUMN norad_id DROP NOT NULL';
          END IF;
          IF EXISTS (SELECT 1 FROM information_schema.columns
                     WHERE table_name='satellites' AND column_name='name') THEN
            EXECUTE 'UPDATE satellites SET object_name = name WHERE object_name IS NULL';
            EXECUTE 'ALTER TABLE satellites ALTER COLUMN name DROP NOT NULL';
          END IF;
        END $$
        """
    )
    op.execute("UPDATE satellites SET object_name = 'NORAD ' || norad_cat_id WHERE object_name IS NULL")
    op.execute("UPDATE satellites SET owner_country = country WHERE owner_country IS NULL")
    op.execute("UPDATE satellites SET country = owner_country WHERE country IS NULL")
    op.execute("UPDATE satellites SET updated_at = NOW() WHERE updated_at IS NULL")
    op.execute("ALTER TABLE satellites ALTER COLUMN updated_at SET NOT NULL")
    op.execute("ALTER TABLE satellites ALTER COLUMN norad_cat_id SET NOT NULL")
    op.execute("ALTER TABLE satellites ALTER COLUMN object_name SET NOT NULL")
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_satellites_norad_cat_id ON satellites(norad_cat_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_satellites_object_name ON satellites(object_name)")
    op.execute(
        """
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
        )
        """
    )
    op.execute(
        """
        ALTER TABLE gp_history
          ADD COLUMN IF NOT EXISTS mean_motion_ddot DOUBLE PRECISION,
          ADD COLUMN IF NOT EXISTS element_set_no INTEGER,
          ADD COLUMN IF NOT EXISTS rev_at_epoch INTEGER,
          ADD COLUMN IF NOT EXISTS fetched_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        """
    )
    op.execute(
        """
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
            risk_tier VARCHAR(10),
            fetched_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT uq_conjunction_pair_tca UNIQUE (norad_cat_id_1, norad_cat_id_2, tca)
        )
        """
    )
    op.execute(
        """
        ALTER TABLE conjunctions
          ADD COLUMN IF NOT EXISTS object_name_1 VARCHAR(255),
          ADD COLUMN IF NOT EXISTS object_name_2 VARCHAR(255),
          ADD COLUMN IF NOT EXISTS dse_1 DOUBLE PRECISION,
          ADD COLUMN IF NOT EXISTS dse_2 DOUBLE PRECISION,
          ADD COLUMN IF NOT EXISTS dilution DOUBLE PRECISION,
          ADD COLUMN IF NOT EXISTS is_constellation_artifact BOOLEAN NOT NULL DEFAULT FALSE,
          ADD COLUMN IF NOT EXISTS risk_weight DOUBLE PRECISION NOT NULL DEFAULT 1.0,
          ADD COLUMN IF NOT EXISTS risk_tier VARCHAR(10),
          ADD COLUMN IF NOT EXISTS fetched_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS model_runs (
            id BIGSERIAL PRIMARY KEY,
            task VARCHAR(100) NOT NULL,
            model_name VARCHAR(100) NOT NULL,
            version VARCHAR(100) NOT NULL,
            params JSONB,
            metrics JSONB,
            trained_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS predictions (
            id BIGSERIAL PRIMARY KEY,
            model_run_id BIGINT REFERENCES model_runs(id),
            norad_cat_id BIGINT,
            target_time TIMESTAMPTZ,
            output JSONB NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_gp_history_norad_epoch ON gp_history(norad_cat_id, epoch DESC)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_conjunctions_tca ON conjunctions(tca)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_conjunctions_risk_tier ON conjunctions(risk_tier)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_predictions_target_time ON predictions(target_time)")


def downgrade() -> None:
    raise RuntimeError("The unified data schema migration is intentionally irreversible.")

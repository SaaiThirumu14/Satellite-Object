CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE IF NOT EXISTS telemetry (
    id BIGSERIAL PRIMARY KEY,
    object_id VARCHAR(128) NOT NULL,
    object_type VARCHAR(64) NOT NULL,
    observed_at TIMESTAMPTZ NOT NULL,
    position geometry(PointZ, 4978) NOT NULL,
    velocity_x DOUBLE PRECISION NOT NULL,
    velocity_y DOUBLE PRECISION NOT NULL,
    velocity_z DOUBLE PRECISION NOT NULL,
    received_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS telemetry_object_time_idx
    ON telemetry (object_id, observed_at DESC);
CREATE INDEX IF NOT EXISTS telemetry_position_idx
    ON telemetry USING GIST (position);

CREATE TABLE IF NOT EXISTS conjunction_alerts (
    id BIGSERIAL PRIMARY KEY,
    object_1_id VARCHAR(128) NOT NULL,
    object_2_id VARCHAR(128) NOT NULL,
    tca TIMESTAMPTZ NOT NULL,
    time_to_tca_seconds DOUBLE PRECISION NOT NULL,
    minimum_separation DOUBLE PRECISION NOT NULL,
    risk_level VARCHAR(16) NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'new',
    created_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS alerts_tca_idx ON conjunction_alerts (tca);
CREATE INDEX IF NOT EXISTS alerts_status_idx ON conjunction_alerts (status);

CREATE TABLE IF NOT EXISTS manoeuvre_logs (
    id BIGSERIAL PRIMARY KEY,
    object_id VARCHAR(128) NOT NULL,
    alert_id BIGINT REFERENCES conjunction_alerts(id),
    manoeuvre_type VARCHAR(64) NOT NULL,
    details JSONB NOT NULL DEFAULT '{}'::jsonb,
    executed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

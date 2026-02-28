CREATE TABLE sensor_config (
    id             BIGSERIAL        PRIMARY KEY,
    sensor_id      VARCHAR(255)     NOT NULL UNIQUE,
    location_label VARCHAR(255),
    latitude       DOUBLE PRECISION NOT NULL,
    longitude      DOUBLE PRECISION NOT NULL,
    sensitivity_k  DOUBLE PRECISION NOT NULL,
    baseline_peak  DOUBLE PRECISION NOT NULL,
    status         VARCHAR(255)     NOT NULL
);

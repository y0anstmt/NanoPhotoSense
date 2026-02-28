CREATE TABLE spectral_reading (
    id            BIGSERIAL        PRIMARY KEY,
    sensor_id     VARCHAR(255)     NOT NULL,
    timestamp     TIMESTAMPTZ      NOT NULL,
    peak_wavelength DOUBLE PRECISION NOT NULL,
    intensities   TEXT             NOT NULL,
    refractive_index DOUBLE PRECISION NOT NULL,
    delta_n       DOUBLE PRECISION NOT NULL,
    risk_score    DOUBLE PRECISION NOT NULL
);
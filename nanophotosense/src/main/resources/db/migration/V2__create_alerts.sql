CREATE TABLE alert (
    id            BIGSERIAL        PRIMARY KEY,
    sensor_id     VARCHAR(255)     NOT NULL,
    timestamp     TIMESTAMPTZ      NOT NULL,
    alert_type    VARCHAR(255)     NOT NULL,
    severity      VARCHAR(255)     NOT NULL,
    alert_message TEXT             NOT NULL,
    acknowledged  BOOLEAN          NOT NULL DEFAULT FALSE
);

-- =============================================================
-- Task 3 — Relational (MySQL) schema for PJME hourly energy data
-- Star schema: two dimension tables + one fact table
--   regions        (dimension) — which grid/zone the reading is for
--   datetime_dim   (dimension) — calendar breakdown of each timestamp
--   energy_readings(fact)      — the measured consumption values
-- =============================================================

CREATE DATABASE IF NOT EXISTS energy_db;
USE energy_db;

-- ---------- Dimension: regions ----------
CREATE TABLE IF NOT EXISTS regions (
    region_id    INT AUTO_INCREMENT PRIMARY KEY,
    region_code  VARCHAR(20)  NOT NULL UNIQUE,   -- e.g. 'PJME'
    region_name  VARCHAR(100) NOT NULL,          -- e.g. 'PJM East'
    description  VARCHAR(255)
);

-- ---------- Dimension: datetime_dim ----------
CREATE TABLE IF NOT EXISTS datetime_dim (
    datetime_id   INT AUTO_INCREMENT PRIMARY KEY,
    full_datetime DATETIME     NOT NULL UNIQUE,   -- the original hourly timestamp
    hour          TINYINT      NOT NULL,          -- 0-23
    day           TINYINT      NOT NULL,          -- 1-31
    month         TINYINT      NOT NULL,          -- 1-12
    year          SMALLINT     NOT NULL,
    day_of_week   TINYINT      NOT NULL,          -- 0 = Monday
    is_weekend    BOOLEAN      NOT NULL,
    INDEX idx_full_datetime (full_datetime),
    INDEX idx_year_month (year, month)
);

-- ---------- Fact: energy_readings ----------
CREATE TABLE IF NOT EXISTS energy_readings (
    reading_id     INT AUTO_INCREMENT PRIMARY KEY,
    datetime_id    INT   NOT NULL,
    region_id      INT   NOT NULL,
    consumption_mw FLOAT NOT NULL,                -- PJME_MW (megawatts)
    created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_reading_datetime
        FOREIGN KEY (datetime_id) REFERENCES datetime_dim(datetime_id)
        ON DELETE CASCADE,
    CONSTRAINT fk_reading_region
        FOREIGN KEY (region_id) REFERENCES regions(region_id)
        ON DELETE CASCADE,
    UNIQUE KEY uq_reading (datetime_id, region_id),
    INDEX idx_region (region_id)
);

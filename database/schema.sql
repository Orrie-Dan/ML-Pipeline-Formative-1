CREATE DATABASE IF NOT EXISTS energy_db;
USE energy_db;

CREATE TABLE IF NOT EXISTS data_sources (
    id INT AUTO_INCREMENT PRIMARY KEY,
    source_name VARCHAR(100) UNIQUE,
    source_type VARCHAR(50),
    description VARCHAR(255),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS energy_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    Datetime DATETIME,
    PJME_MW FLOAT,
    Hour INT,
    Day INT,
    Month INT,
    Year INT,
    DayOfWeek INT,
    source_id INT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_datetime (Datetime),
    CONSTRAINT fk_energy_source
        FOREIGN KEY (source_id)
        REFERENCES data_sources(id)
        ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS prediction_runs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    run_time DATETIME,
    model_name VARCHAR(120),
    feature_count INT,
    predicted_value FLOAT,
    source_record_id INT NULL,
    notes VARCHAR(255),
    CONSTRAINT fk_prediction_record
        FOREIGN KEY (source_record_id)
        REFERENCES energy_records(id)
        ON DELETE SET NULL
);

-- Example queries (SQL)
SELECT * FROM energy_records ORDER BY Datetime DESC LIMIT 1;
SELECT COUNT(*) AS records_last_7_days FROM energy_records WHERE Datetime >= NOW() - INTERVAL 7 DAY;
SELECT Month, AVG(PJME_MW) AS avg_mw FROM energy_records GROUP BY Month ORDER BY Month;

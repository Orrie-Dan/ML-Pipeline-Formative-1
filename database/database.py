import os
from datetime import datetime
from pathlib import Path

import mysql.connector

from database.common import load_env_file

ENV_PATH = Path(__file__).resolve().parent.parent / ".env"


load_env_file(ENV_PATH)

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", "your_password"),
    "database": os.getenv("DB_NAME", "energy_db"),
}

TABLE_NAME = "energy_records"
SOURCE_TABLE = "data_sources"
PREDICTION_TABLE = "prediction_runs"
TRAINING_COLUMNS = [
    "Datetime",
    "PJME_MW",
    "Hour",
    "Day",
    "Month",
    "Year",
    "DayOfWeek",
]


def ensure_table_schema(cursor):
    cursor.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {SOURCE_TABLE} (
            id INT AUTO_INCREMENT PRIMARY KEY,
            source_name VARCHAR(100) UNIQUE,
            source_type VARCHAR(50),
            description VARCHAR(255),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    cursor.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
            id INT AUTO_INCREMENT PRIMARY KEY,
            `Datetime` DATETIME,
            `PJME_MW` FLOAT,
            `Hour` INT,
            `Day` INT,
            `Month` INT,
            `Year` INT,
            `DayOfWeek` INT,
            source_id INT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_datetime (`Datetime`),
            CONSTRAINT fk_energy_source
                FOREIGN KEY (source_id)
                REFERENCES data_sources(id)
                ON DELETE SET NULL
        )
        """
    )

    cursor.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {PREDICTION_TABLE} (
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
        )
        """
    )

    cursor.execute(f"SHOW COLUMNS FROM {TABLE_NAME}")
    existing_columns = {row[0] for row in cursor.fetchall()}

    rename_map = {
        "timestamp": "Datetime",
        "value": "PJME_MW",
        "hour": "Hour",
        "dayofweek": "DayOfWeek",
        "month": "Month",
    }

    for old_name, new_name in rename_map.items():
        if old_name in existing_columns and new_name not in existing_columns:
            cursor.execute(
                f"ALTER TABLE {TABLE_NAME} CHANGE COLUMN `{old_name}` `{new_name}` "
                + (
                    "DATETIME"
                    if new_name == "Datetime"
                    else "FLOAT"
                    if new_name == "PJME_MW"
                    else "INT"
                )
            )
            existing_columns.discard(old_name)
            existing_columns.add(new_name)

    for column_name in ("Day", "Year"):
        if column_name not in existing_columns:
            cursor.execute(f"ALTER TABLE {TABLE_NAME} ADD COLUMN `{column_name}` INT NULL")
            existing_columns.add(column_name)

    if "source_id" not in existing_columns:
        cursor.execute(f"ALTER TABLE {TABLE_NAME} ADD COLUMN source_id INT NULL")
        existing_columns.add("source_id")

    if "created_at" not in existing_columns:
        cursor.execute(
            f"ALTER TABLE {TABLE_NAME} ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP"
        )


def get_connection():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        ensure_table_schema(cursor)
        conn.commit()
        return conn, cursor
    except mysql.connector.Error as exc:
        raise RuntimeError(f"Unable to connect to MySQL database: {exc}") from exc


def get_or_create_source(cursor, source_name, source_type="api", description=None):
    cursor.execute(f"SELECT id FROM {SOURCE_TABLE} WHERE source_name = %s", (source_name,))
    row = cursor.fetchone()
    if row:
        return row[0]

    cursor.execute(
        f"INSERT INTO {SOURCE_TABLE} (source_name, source_type, description) VALUES (%s, %s, %s)",
        (source_name, source_type, description),
    )
    return cursor.lastrowid

# -----------------------
# INSERT RECORD
# -----------------------
def insert_record(
    record_datetime,
    pjme_mw,
    hour,
    day,
    month,
    year,
    dayofweek,
    source_name="api_input",
    source_type="api",
):
    conn, cursor = get_connection()
    source_id = get_or_create_source(cursor, source_name, source_type=source_type)
    sql = """
    INSERT INTO energy_records (`Datetime`, `PJME_MW`, `Hour`, `Day`, `Month`, `Year`, `DayOfWeek`, source_id)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """
    cursor.execute(
        sql,
        (record_datetime, float(pjme_mw), hour, day, month, year, dayofweek, source_id),
    )
    inserted_id = cursor.lastrowid
    conn.commit()
    cursor.close()
    conn.close()
    return inserted_id


def log_prediction_run(run_time, model_name, feature_count, predicted_value, source_record_id=None, notes=None):
    conn, cursor = get_connection()
    cursor.execute(
        f"""
        INSERT INTO {PREDICTION_TABLE} (run_time, model_name, feature_count, predicted_value, source_record_id, notes)
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (run_time, model_name, int(feature_count), float(predicted_value), source_record_id, notes),
    )
    conn.commit()
    cursor.close()
    conn.close()


def _row_to_record(row):
    return {
        "id": row[0],
        "datetime": row[1],
        "pjme_mw": row[2],
        "hour": row[3],
        "day": row[4],
        "month": row[5],
        "year": row[6],
        "dayofweek": row[7],
        "source_id": row[8] if len(row) > 8 else None,
    }


def get_record_by_id(record_id):
    conn, cursor = get_connection()
    cursor.execute(
        f"SELECT id, `Datetime`, `PJME_MW`, `Hour`, `Day`, `Month`, `Year`, `DayOfWeek`, source_id FROM {TABLE_NAME} WHERE id = %s",
        (record_id,),
    )
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return _row_to_record(row) if row else None


def get_latest_record():
    conn, cursor = get_connection()
    cursor.execute(
        f"SELECT id, `Datetime`, `PJME_MW`, `Hour`, `Day`, `Month`, `Year`, `DayOfWeek`, source_id FROM {TABLE_NAME} ORDER BY `Datetime` DESC, id DESC LIMIT 1"
    )
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return _row_to_record(row) if row else None


def get_records_by_date_range(start_datetime, end_datetime):
    conn, cursor = get_connection()
    cursor.execute(
        f"SELECT id, `Datetime`, `PJME_MW`, `Hour`, `Day`, `Month`, `Year`, `DayOfWeek`, source_id FROM {TABLE_NAME} WHERE `Datetime` BETWEEN %s AND %s ORDER BY `Datetime` ASC, id ASC",
        (start_datetime, end_datetime),
    )
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return [_row_to_record(row) for row in rows]


def update_record_by_id(record_id, record_datetime, pjme_mw, hour, day, month, year, dayofweek):
    conn, cursor = get_connection()
    cursor.execute(
        f"""
        UPDATE {TABLE_NAME}
        SET `Datetime` = %s,
            `PJME_MW` = %s,
            `Hour` = %s,
            `Day` = %s,
            `Month` = %s,
            `Year` = %s,
            `DayOfWeek` = %s
        WHERE id = %s
        """,
        (record_datetime, float(pjme_mw), hour, day, month, year, dayofweek, record_id),
    )
    conn.commit()
    affected_rows = cursor.rowcount
    cursor.close()
    conn.close()
    return affected_rows > 0


def delete_record_by_id(record_id):
    conn, cursor = get_connection()
    cursor.execute(f"DELETE FROM {TABLE_NAME} WHERE id = %s", (record_id,))
    conn.commit()
    affected_rows = cursor.rowcount
    cursor.close()
    conn.close()
    return affected_rows > 0


# -----------------------
# GET HISTORY
# -----------------------
def get_all_values():
    conn, cursor = get_connection()
    cursor.execute(f"SELECT `PJME_MW` FROM {TABLE_NAME} ORDER BY `Datetime` ASC, id ASC")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return [r[0] for r in rows]
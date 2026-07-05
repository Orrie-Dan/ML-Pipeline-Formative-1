"""Load the real PJME dataset (clean_energy_dataset.csv) into MySQL.

Populates the star schema created by schema.sql:
    regions  ->  datetime_dim  ->  energy_readings

Usage:
    python sql_loader.py                # load the whole dataset
    python sql_loader.py --limit 5000   # load only the first 5000 rows (demo)
    python sql_loader.py --limit 5000 --reset   # drop + recreate tables first
"""
from __future__ import annotations

import argparse

import mysql.connector
import pandas as pd

from db_config import (
    CSV_PATH,
    REGION_CODE,
    REGION_DESCRIPTION,
    REGION_NAME,
    SCHEMA_PATH,
    get_mysql_config,
)

BATCH_SIZE = 2000


def run_schema(cursor) -> None:
    """Execute schema.sql statement by statement."""
    statements = [s.strip() for s in SCHEMA_PATH.read_text().split(";") if s.strip()]
    for stmt in statements:
        # skip pure comment blocks
        if all(line.strip().startswith("--") or not line.strip() for line in stmt.splitlines()):
            continue
        # A hosted MySQL (e.g. Railway) connects to a pre-created database and may
        # not grant CREATE DATABASE / USE privileges — the connection already
        # targets DB_NAME, so skip those statements and just create the tables.
        first_word = stmt.lstrip().split(None, 1)[0].upper()
        if first_word == "USE" or stmt.lstrip().upper().startswith("CREATE DATABASE"):
            continue
        cursor.execute(stmt)


def get_or_create_region(cursor) -> int:
    cursor.execute("SELECT region_id FROM regions WHERE region_code = %s", (REGION_CODE,))
    row = cursor.fetchone()
    if row:
        return row[0]
    cursor.execute(
        "INSERT INTO regions (region_code, region_name, description) VALUES (%s, %s, %s)",
        (REGION_CODE, REGION_NAME, REGION_DESCRIPTION),
    )
    return cursor.lastrowid


def load(limit: int | None, reset: bool) -> None:
    print(f"Reading {CSV_PATH} ...")
    df = pd.read_csv(CSV_PATH, parse_dates=["Datetime"])
    df = df.sort_values("Datetime").drop_duplicates(subset=["Datetime"])
    if limit:
        df = df.head(limit)
    print(f"Rows to load: {len(df):,}")

    conn = mysql.connector.connect(**get_mysql_config())
    cursor = conn.cursor()

    if reset:
        print("Dropping existing tables (energy_readings, datetime_dim, regions) ...")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
        for table in ("energy_readings", "datetime_dim", "regions"):
            cursor.execute(f"DROP TABLE IF EXISTS {table}")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1")

    print("Ensuring schema ...")
    run_schema(cursor)
    conn.commit()

    region_id = get_or_create_region(cursor)
    conn.commit()
    print(f"region_id for {REGION_CODE}: {region_id}")

    # 1) Insert datetime_dim rows (idempotent via INSERT IGNORE on the UNIQUE full_datetime).
    print("Inserting datetime_dim ...")
    dt_rows = [
        (
            row.Datetime.to_pydatetime(),
            int(row.Hour),
            int(row.Day),
            int(row.Month),
            int(row.Year),
            int(row.DayOfWeek),
            1 if int(row.DayOfWeek) in (5, 6) else 0,
        )
        for row in df.itertuples(index=False)
    ]
    dt_sql = (
        "INSERT IGNORE INTO datetime_dim "
        "(full_datetime, hour, day, month, year, day_of_week, is_weekend) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s)"
    )
    for i in range(0, len(dt_rows), BATCH_SIZE):
        cursor.executemany(dt_sql, dt_rows[i : i + BATCH_SIZE])
        conn.commit()
    print(f"datetime_dim done ({len(dt_rows):,} rows attempted).")

    # 2) Map full_datetime -> datetime_id so we can build the fact rows.
    print("Building datetime_id map ...")
    cursor.execute("SELECT datetime_id, full_datetime FROM datetime_dim")
    id_map = {full_dt: dt_id for dt_id, full_dt in cursor.fetchall()}

    # 3) Insert the fact table.
    print("Inserting energy_readings ...")
    fact_rows = [
        (id_map[row.Datetime.to_pydatetime()], region_id, float(row.PJME_MW))
        for row in df.itertuples(index=False)
        if row.Datetime.to_pydatetime() in id_map
    ]
    fact_sql = (
        "INSERT IGNORE INTO energy_readings (datetime_id, region_id, consumption_mw) "
        "VALUES (%s, %s, %s)"
    )
    for i in range(0, len(fact_rows), BATCH_SIZE):
        cursor.executemany(fact_sql, fact_rows[i : i + BATCH_SIZE])
        conn.commit()
    print(f"energy_readings done ({len(fact_rows):,} rows attempted).")

    cursor.execute("SELECT COUNT(*) FROM energy_readings")
    print(f"Total rows now in energy_readings: {cursor.fetchone()[0]:,}")

    cursor.close()
    conn.close()
    print("Load complete.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Load PJME CSV into MySQL star schema")
    parser.add_argument("--limit", type=int, default=None, help="Load only the first N rows")
    parser.add_argument("--reset", action="store_true", help="Drop and recreate tables first")
    args = parser.parse_args()
    load(args.limit, args.reset)

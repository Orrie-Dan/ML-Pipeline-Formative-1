"""Load the real PJME dataset into MongoDB as denormalized documents.

Unlike the SQL star schema (which splits region / calendar / measurement into
three joined tables), the MongoDB design embeds everything the application
reads together into a single self-describing document per hourly reading.

Usage:
    python mongo_loader.py                # load the whole dataset
    python mongo_loader.py --limit 5000   # load only the first 5000 rows (demo)
    python mongo_loader.py --limit 5000 --reset   # empty the collection first
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone

import pandas as pd
from pymongo import ASCENDING, MongoClient

from db_config import (
    CSV_PATH,
    REGION_CODE,
    REGION_NAME,
    get_mongo_config,
)

BATCH_SIZE = 5000


def build_document(row) -> dict:
    dow = int(row.DayOfWeek)
    return {
        "region": {"code": REGION_CODE, "name": REGION_NAME},
        "datetime": row.Datetime.to_pydatetime(),
        "consumption_mw": float(row.PJME_MW),
        "calendar": {
            "hour": int(row.Hour),
            "day": int(row.Day),
            "month": int(row.Month),
            "year": int(row.Year),
            "day_of_week": dow,
            "is_weekend": dow in (5, 6),
        },
        "created_at": datetime.now(timezone.utc),
    }


def load(limit: int | None, reset: bool) -> None:
    cfg = get_mongo_config()
    print(f"Reading {CSV_PATH} ...")
    df = pd.read_csv(CSV_PATH, parse_dates=["Datetime"])
    df = df.sort_values("Datetime").drop_duplicates(subset=["Datetime"])
    if limit:
        df = df.head(limit)
    print(f"Rows to load: {len(df):,}")

    client = MongoClient(cfg["uri"])
    collection = client[cfg["db_name"]][cfg["collection"]]

    if reset:
        print(f"Clearing collection '{cfg['collection']}' ...")
        collection.delete_many({})

    docs = [build_document(row) for row in df.itertuples(index=False)]
    for i in range(0, len(docs), BATCH_SIZE):
        collection.insert_many(docs[i : i + BATCH_SIZE])
        print(f"  inserted {min(i + BATCH_SIZE, len(docs)):,}/{len(docs):,}")

    collection.create_index([("datetime", ASCENDING)], name="idx_datetime")
    collection.create_index([("calendar.year", ASCENDING), ("calendar.month", ASCENDING)],
                            name="idx_year_month")

    print(f"Total documents now in collection: {collection.count_documents({}):,}")
    client.close()
    print("Load complete.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Load PJME CSV into MongoDB")
    parser.add_argument("--limit", type=int, default=None, help="Load only the first N rows")
    parser.add_argument("--reset", action="store_true", help="Empty the collection first")
    args = parser.parse_args()
    load(args.limit, args.reset)

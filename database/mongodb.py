import os
from datetime import datetime
from pathlib import Path

ENV_PATH = Path(__file__).resolve().parent.parent / ".env"


def load_env_file(path):
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


load_env_file(ENV_PATH)

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "energy_db")
MONGO_COLLECTION = os.getenv("MONGO_COLLECTION", "energy_records")

try:
    from pymongo import ASCENDING, DESCENDING, MongoClient
    from pymongo.errors import PyMongoError
except Exception:  # pragma: no cover - optional dependency/runtime
    MongoClient = None
    ASCENDING = 1
    DESCENDING = -1
    PyMongoError = Exception


def _require_mongo_client():
    if MongoClient is None:
        raise RuntimeError("pymongo is not installed. Install with: pip install pymongo")


def _get_collection():
    _require_mongo_client()
    client = MongoClient(MONGO_URI)
    db = client[MONGO_DB_NAME]
    collection = db[MONGO_COLLECTION]
    collection.create_index([("datetime", ASCENDING)], name="idx_datetime")
    return client, collection


def _doc_to_record(doc):
    return {
        "id": str(doc.get("_id")),
        "datetime": doc.get("datetime"),
        "pjme_mw": doc.get("pjme_mw"),
        "hour": doc.get("hour"),
        "day": doc.get("day"),
        "month": doc.get("month"),
        "year": doc.get("year"),
        "dayofweek": doc.get("dayofweek"),
        "source": doc.get("source"),
        "created_at": doc.get("created_at"),
    }


def insert_record_mongo(record_datetime, pjme_mw, hour, day, month, year, dayofweek, source="api_input"):
    client, collection = _get_collection()
    try:
        payload = {
            "datetime": record_datetime,
            "pjme_mw": float(pjme_mw),
            "hour": int(hour),
            "day": int(day),
            "month": int(month),
            "year": int(year),
            "dayofweek": int(dayofweek),
            "source": source,
            "created_at": datetime.utcnow(),
        }
        result = collection.insert_one(payload)
        return str(result.inserted_id)
    except PyMongoError as exc:
        raise RuntimeError(f"Unable to write to MongoDB: {exc}") from exc
    finally:
        client.close()


def get_latest_record_mongo():
    client, collection = _get_collection()
    try:
        doc = collection.find_one(sort=[("datetime", DESCENDING), ("_id", DESCENDING)])
        return _doc_to_record(doc) if doc else None
    except PyMongoError as exc:
        raise RuntimeError(f"Unable to read from MongoDB: {exc}") from exc
    finally:
        client.close()


def get_records_by_date_range_mongo(start_datetime, end_datetime):
    client, collection = _get_collection()
    try:
        cursor = collection.find(
            {"datetime": {"$gte": start_datetime, "$lte": end_datetime}}
        ).sort([("datetime", ASCENDING), ("_id", ASCENDING)])
        return [_doc_to_record(doc) for doc in cursor]
    except PyMongoError as exc:
        raise RuntimeError(f"Unable to query MongoDB: {exc}") from exc
    finally:
        client.close()


def get_record_by_id_mongo(record_id):
    _require_mongo_client()
    from bson import ObjectId

    client, collection = _get_collection()
    try:
        doc = collection.find_one({"_id": ObjectId(record_id)})
        return _doc_to_record(doc) if doc else None
    except Exception as exc:
        raise RuntimeError(f"Unable to read MongoDB record: {exc}") from exc
    finally:
        client.close()


def update_record_by_id_mongo(record_id, record_datetime, pjme_mw, hour, day, month, year, dayofweek):
    _require_mongo_client()
    from bson import ObjectId

    client, collection = _get_collection()
    try:
        result = collection.update_one(
            {"_id": ObjectId(record_id)},
            {
                "$set": {
                    "datetime": record_datetime,
                    "pjme_mw": float(pjme_mw),
                    "hour": int(hour),
                    "day": int(day),
                    "month": int(month),
                    "year": int(year),
                    "dayofweek": int(dayofweek),
                }
            },
        )
        return result.matched_count > 0
    except Exception as exc:
        raise RuntimeError(f"Unable to update MongoDB record: {exc}") from exc
    finally:
        client.close()


def delete_record_by_id_mongo(record_id):
    _require_mongo_client()
    from bson import ObjectId

    client, collection = _get_collection()
    try:
        result = collection.delete_one({"_id": ObjectId(record_id)})
        return result.deleted_count > 0
    except Exception as exc:
        raise RuntimeError(f"Unable to delete MongoDB record: {exc}") from exc
    finally:
        client.close()


def get_all_values_mongo():
    client, collection = _get_collection()
    try:
        cursor = collection.find({}, {"pjme_mw": 1}).sort([("datetime", ASCENDING), ("_id", ASCENDING)])
        return [float(doc["pjme_mw"]) for doc in cursor if "pjme_mw" in doc]
    except PyMongoError as exc:
        raise RuntimeError(f"Unable to fetch MongoDB history: {exc}") from exc
    finally:
        client.close()

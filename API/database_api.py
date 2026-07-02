from datetime import datetime
from pathlib import Path
import sys

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from database.database import (
    delete_record_by_id,
    get_latest_record,
    get_record_by_id,
    get_records_by_date_range,
    insert_record,
    update_record_by_id,
)
from database.mongodb import (
    delete_record_by_id_mongo,
    get_latest_record_mongo,
    get_record_by_id_mongo,
    get_records_by_date_range_mongo,
    insert_record_mongo,
    update_record_by_id_mongo,
)

app = FastAPI(title="Energy Database API")


class EnergyRecordInput(BaseModel):
    datetime: datetime
    pjme_mw: float
    hour: int
    day: int
    month: int
    year: int
    dayofweek: int


class EnergyRecordUpdateInput(BaseModel):
    datetime: datetime
    pjme_mw: float
    hour: int
    day: int
    month: int
    year: int
    dayofweek: int


@app.post("/records")
def create_record(record: EnergyRecordInput):
    try:
        sql_id = insert_record(
            record.datetime,
            record.pjme_mw,
            record.hour,
            record.day,
            record.month,
            record.year,
            record.dayofweek,
            source_name="database_api",
            source_type="api",
        )
        mongo_id = insert_record_mongo(
            record.datetime,
            record.pjme_mw,
            record.hour,
            record.day,
            record.month,
            record.year,
            record.dayofweek,
            source="database_api",
        )
        return {
            "message": "Record created in SQL and MongoDB",
            "record": record.model_dump(),
            "sql_id": sql_id,
            "mongo_id": mongo_id,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/sql/records")
def create_record_sql(record: EnergyRecordInput):
    try:
        sql_id = insert_record(
            record.datetime,
            record.pjme_mw,
            record.hour,
            record.day,
            record.month,
            record.year,
            record.dayofweek,
            source_name="database_api_sql",
            source_type="api",
        )
        return {"message": "SQL record created", "sql_id": sql_id, "record": record.model_dump()}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/mongo/records")
def create_record_mongo(record: EnergyRecordInput):
    try:
        mongo_id = insert_record_mongo(
            record.datetime,
            record.pjme_mw,
            record.hour,
            record.day,
            record.month,
            record.year,
            record.dayofweek,
            source="database_api_mongo",
        )
        return {"message": "Mongo record created", "mongo_id": mongo_id, "record": record.model_dump()}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/records/latest")
def read_latest_record():
    try:
        record = get_latest_record()
        if record is None:
            raise HTTPException(status_code=404, detail="No records found")
        return record
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/mongo/records/latest")
def read_latest_record_mongo():
    try:
        record = get_latest_record_mongo()
        if record is None:
            raise HTTPException(status_code=404, detail="No Mongo records found")
        return record
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/records")
def read_records(start_datetime: datetime, end_datetime: datetime):
    try:
        return get_records_by_date_range(start_datetime, end_datetime)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/mongo/records")
def read_records_mongo(start_datetime: datetime, end_datetime: datetime):
    try:
        return get_records_by_date_range_mongo(start_datetime, end_datetime)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/records/{record_id}")
def read_record(record_id: int):
    try:
        record = get_record_by_id(record_id)
        if record is None:
            raise HTTPException(status_code=404, detail="Record not found")
        return record
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/mongo/records/{record_id}")
def read_record_mongo(record_id: str):
    try:
        record = get_record_by_id_mongo(record_id)
        if record is None:
            raise HTTPException(status_code=404, detail="Mongo record not found")
        return record
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.put("/records/{record_id}")
def update_record(record_id: int, record: EnergyRecordUpdateInput):
    try:
        updated = update_record_by_id(
            record_id,
            record.datetime,
            record.pjme_mw,
            record.hour,
            record.day,
            record.month,
            record.year,
            record.dayofweek,
        )
        if not updated:
            raise HTTPException(status_code=404, detail="Record not found")
        return {"message": "Record updated successfully", "record_id": record_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.put("/mongo/records/{record_id}")
def update_record_mongo(record_id: str, record: EnergyRecordUpdateInput):
    try:
        updated = update_record_by_id_mongo(
            record_id,
            record.datetime,
            record.pjme_mw,
            record.hour,
            record.day,
            record.month,
            record.year,
            record.dayofweek,
        )
        if not updated:
            raise HTTPException(status_code=404, detail="Mongo record not found")
        return {"message": "Mongo record updated successfully", "record_id": record_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/records/{record_id}")
def delete_record(record_id: int):
    try:
        deleted = delete_record_by_id(record_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Record not found")
        return {"message": "Record deleted successfully", "record_id": record_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/mongo/records/{record_id}")
def delete_record_mongo(record_id: str):
    try:
        deleted = delete_record_by_id_mongo(record_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Mongo record not found")
        return {"message": "Mongo record deleted successfully", "record_id": record_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

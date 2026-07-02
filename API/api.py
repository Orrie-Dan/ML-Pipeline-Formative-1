from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import joblib
import numpy as np
from datetime import datetime
from pathlib import Path
import sys

app = FastAPI(title="Energy Prediction API")

# -----------------------
# LOAD MODEL
# -----------------------
BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from database.database import get_all_values, insert_record
from database.database import log_prediction_run
from database.mongodb import get_all_values_mongo, insert_record_mongo

model = joblib.load(PROJECT_ROOT / "models" / "ridge_energy_model.joblib")
feature_columns = joblib.load(PROJECT_ROOT / "models" / "feature_columns.joblib")


# -----------------------
# INPUT
# -----------------------
class PredictionInput(BaseModel):
    hour: int
    dayofweek: int
    month: int


# -----------------------
# BUILD FEATURES
# -----------------------
def build_lags(values):
    if len(values) < 168:
        raise ValueError("Not enough history for lag features")

    lag_1h = values[-1]
    lag_24h_feat = values[-24]
    lag_168h_feat = values[-168]
    ma_24h = np.mean(values[-24:])
    ma_168h = np.mean(values[-168:])

    return lag_1h, lag_24h_feat, lag_168h_feat, ma_24h, ma_168h


def build_model_features(data, lag_values):
    lag_1h, lag_24h_feat, lag_168h_feat, ma_24h, ma_168h = lag_values

    feature_map = {
        "Hour": data.hour,
        "DayOfWeek": data.dayofweek,
        "Month": data.month,
        "lag_1h": lag_1h,
        "lag_24h_feat": lag_24h_feat,
        "lag_168h_feat": lag_168h_feat,
        "ma_24h": ma_24h,
        "ma_168h": ma_168h,
    }

    missing_columns = [column for column in feature_columns if column not in feature_map]
    if missing_columns:
        raise ValueError(f"Missing model features: {missing_columns}")

    return np.array([[feature_map[column] for column in feature_columns]], dtype=float)


# -----------------------
# PREDICT
# -----------------------
@app.post("/predict")
def predict(data: PredictionInput):

    try:
        values = get_all_values()
        history_source = "sql"
        if len(values) < 168:
            values = get_all_values_mongo()
            history_source = "mongo"

        if len(values) < 168:
            raise ValueError(
                "Not enough history to build lag features. Seed at least 168 hourly records in SQL or MongoDB."
            )

        lag_values = build_lags(values)
        features = build_model_features(data, lag_values)

        prediction = model.predict(features)[0]

        now = datetime.now()
        sql_record_id = insert_record(
            now,
            prediction,
            now.hour,
            now.day,
            now.month,
            now.year,
            now.weekday(),
            source_name="prediction_api",
            source_type="prediction",
        )
        insert_record_mongo(
            now,
            prediction,
            now.hour,
            now.day,
            now.month,
            now.year,
            now.weekday(),
            source="prediction_api",
        )

        log_prediction_run(
            run_time=now,
            model_name="ridge_energy_model.joblib",
            feature_count=len(feature_columns),
            predicted_value=prediction,
            source_record_id=sql_record_id,
            notes=f"history_source={history_source}",
        )

        return {
            "predicted_energy_mw": float(prediction),
            "lag_used": True,
            "features_used": feature_columns,
            "history_source": history_source,
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
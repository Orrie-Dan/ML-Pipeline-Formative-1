from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import joblib
import numpy as np
import pandas as pd
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

model = joblib.load(PROJECT_ROOT / "models" / "ridge_energy_model.joblib")
feature_columns = joblib.load(PROJECT_ROOT / "models" / "feature_columns.joblib")
CSV_PATH = PROJECT_ROOT / "clean_energy_dataset.csv"


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


def get_all_values_csv():
    df = pd.read_csv(CSV_PATH, parse_dates=["Datetime"])
    df = df.sort_values("Datetime")
    return df["PJME_MW"].tolist()


def append_prediction_to_csv(prediction):
    df = pd.read_csv(CSV_PATH, parse_dates=["Datetime"])
    df = df.sort_values("Datetime")

    last_time = df.iloc[-1]["Datetime"]
    next_time = last_time + pd.Timedelta(hours=1)

    new_row = {
        "Datetime": next_time,
        "PJME_MW": float(prediction),
        "Hour": next_time.hour,
        "Day": next_time.day,
        "Month": next_time.month,
        "Year": next_time.year,
        "DayOfWeek": next_time.dayofweek,
    }

    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df.to_csv(CSV_PATH, index=False)


# -----------------------
# PREDICT
# -----------------------
@app.post("/predict")
def predict(data: PredictionInput):

    try:
        values = get_all_values_csv()
        history_source = "csv"
        if len(values) < 168:
            raise ValueError("Not enough history to build lag features. Seed at least 168 hourly records in the CSV.")

        lag_values = build_lags(values)
        features = build_model_features(data, lag_values)

        prediction = model.predict(features)[0]

        append_prediction_to_csv(float(prediction))

        return {
            "predicted_energy_mw": float(prediction),
            "lag_used": True,
            "features_used": feature_columns,
            "history_source": history_source,
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
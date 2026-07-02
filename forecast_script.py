from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import urlopen

import joblib
import numpy as np
import pandas as pd


def fetch_latest_record(api_base_url: str) -> dict[str, Any]:
    url = f"{api_base_url.rstrip('/')}/records/latest"
    with urlopen(url) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_records_by_range(api_base_url: str, start_dt: datetime, end_dt: datetime) -> list[dict[str, Any]]:
    query = urlencode(
        {
            "start_datetime": start_dt.isoformat(),
            "end_datetime": end_dt.isoformat(),
        }
    )
    url = f"{api_base_url.rstrip('/')}/records?{query}"
    with urlopen(url) as response:
        return json.loads(response.read().decode("utf-8"))


def preprocess_records(records: list[dict[str, Any]]) -> pd.DataFrame:
    if not records:
        raise ValueError("No records were returned by the API")

    df = pd.DataFrame(records)

    # Match Task 1 style: parse time, sort, drop duplicates, and handle missing values.
    df = df.rename(columns={"datetime": "Datetime", "pjme_mw": "PJME_MW"})
    df["Datetime"] = pd.to_datetime(df["Datetime"], errors="coerce")
    df = df.dropna(subset=["Datetime"]).sort_values("Datetime").drop_duplicates(subset=["Datetime"])

    df["PJME_MW"] = pd.to_numeric(df["PJME_MW"], errors="coerce")
    df["PJME_MW"] = df["PJME_MW"].interpolate(method="linear", limit_direction="both")

    df["Hour"] = df["Datetime"].dt.hour
    df["Day"] = df["Datetime"].dt.day
    df["Month"] = df["Datetime"].dt.month
    df["Year"] = df["Datetime"].dt.year
    df["DayOfWeek"] = df["Datetime"].dt.dayofweek

    return df.reset_index(drop=True)


def build_next_hour_features(df: pd.DataFrame) -> tuple[dict[str, float], datetime]:
    if len(df) < 168:
        raise ValueError("Need at least 168 hourly records to create lag and moving-average features")

    values = df["PJME_MW"].to_numpy(dtype=float)
    latest_ts = df["Datetime"].iloc[-1]
    forecast_ts = latest_ts + timedelta(hours=1)

    features = {
        "Hour": float(forecast_ts.hour),
        "DayOfWeek": float(forecast_ts.dayofweek),
        "Month": float(forecast_ts.month),
        "lag_1h": float(values[-1]),
        "lag_24h_feat": float(values[-24]),
        "lag_168h_feat": float(values[-168]),
        "ma_24h": float(np.mean(values[-24:])),
        "ma_168h": float(np.mean(values[-168:])),
    }

    return features, forecast_ts


def predict_with_model(project_root: Path, features: dict[str, float]) -> tuple[float, list[str]]:
    model = joblib.load(project_root / "models" / "ridge_energy_model.joblib")
    feature_columns = joblib.load(project_root / "models" / "feature_columns.joblib")

    missing = [col for col in feature_columns if col not in features]
    if missing:
        raise ValueError(f"Missing required model features: {missing}")

    x = np.array([[features[col] for col in feature_columns]], dtype=float)
    prediction = float(model.predict(x)[0])
    return prediction, feature_columns


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch API data, preprocess, and forecast next-hour energy demand")
    parser.add_argument(
        "--api-base-url",
        default="http://127.0.0.1:8001",
        help="Base URL for the database CRUD API (default: http://127.0.0.1:8001)",
    )
    parser.add_argument(
        "--history-hours",
        type=int,
        default=240,
        help="How many recent hours to request from API (minimum 168, default: 240)",
    )
    args = parser.parse_args()

    if args.history_hours < 168:
        raise ValueError("--history-hours must be at least 168")

    project_root = Path(__file__).resolve().parent

    latest = fetch_latest_record(args.api_base_url)
    latest_dt = datetime.fromisoformat(str(latest["datetime"]).replace("Z", "+00:00"))
    start_dt = latest_dt - timedelta(hours=args.history_hours - 1)

    records = fetch_records_by_range(args.api_base_url, start_dt, latest_dt)
    df = preprocess_records(records)
    features, forecast_ts = build_next_hour_features(df)
    prediction, ordered_columns = predict_with_model(project_root, features)

    print("Forecast pipeline completed")
    print(f"Records fetched: {len(records)}")
    print(f"Records after preprocessing: {len(df)}")
    print(f"Forecast timestamp: {forecast_ts.isoformat()}")
    print(f"Predicted PJME_MW: {prediction:.3f}")
    print("Feature order used by model:")
    print(ordered_columns)


if __name__ == "__main__":
    main()

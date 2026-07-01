"""
Data Loader - Downloads and processes NYC TLC taxi trip data
for training the dynamic pricing model.

Usage:
    python -m ml.data_loader
"""

import pandas as pd
import numpy as np
import os
import logging
import urllib.request

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")


def download_tlc_data(year: int = 2024, month: int = 1) -> str:
    """Download NYC TLC Yellow Taxi trip data (Parquet format)."""
    filename = f"yellow_tripdata_{year}-{month:02d}.parquet"
    url = f"https://d37ci6vzurychx.cloudfront.net/trip-data/{filename}"
    filepath = os.path.join(DATA_DIR, filename)

    if os.path.exists(filepath):
        logger.info("File already exists: %s", filepath)
        return filepath

    logger.info("Downloading %s ...", url)
    os.makedirs(DATA_DIR, exist_ok=True)
    urllib.request.urlretrieve(url, filepath)
    logger.info("Downloaded to %s", filepath)
    return filepath


def process_tlc_data(filepath: str, sample_size: int = 50000) -> pd.DataFrame:
    """Process raw TLC data into training format."""
    logger.info("Loading parquet file...")
    df = pd.read_parquet(filepath)
    logger.info("Raw data shape: %s", df.shape)

    df = df[
        (df["trip_distance"] > 0.5) &
        (df["trip_distance"] < 50) &
        (df["fare_amount"] > 2.5) &
        (df["fare_amount"] < 500) &
        (df["tpep_pickup_datetime"].notna()) &
        (df["tpep_dropoff_datetime"].notna())
    ].copy()

    df["hour"] = df["tpep_pickup_datetime"].dt.hour
    df["distance"] = df["trip_distance"] * 1.60934
    df["duration_minutes"] = (
        df["tpep_dropoff_datetime"] - df["tpep_pickup_datetime"]
    ).dt.total_seconds() / 60
    df = df[(df["duration_minutes"] > 1) & (df["duration_minutes"] < 180)]
    df["speed_kmh"] = df["distance"] / (df["duration_minutes"] / 60)

    def estimate_traffic(speed):
        if speed > 40: return "low"
        elif speed > 20: return "medium"
        else: return "high"

    df["traffic"] = df["speed_kmh"].apply(estimate_traffic)

    weather_probs = {"clear": 0.55, "rain": 0.30, "snow": 0.15}
    np.random.seed(42)
    df["weather"] = np.random.choice(
        list(weather_probs.keys()), size=len(df), p=list(weather_probs.values())
    )
    df["price"] = df["total_amount"]

    output_cols = ["distance", "hour", "weather", "traffic", "price"]
    df_final = df[output_cols].dropna()
    if len(df_final) > sample_size:
        df_final = df_final.sample(n=sample_size, random_state=42)

    logger.info("Processed data shape: %s", df_final.shape)
    return df_final


def run():
    """Download and process TLC data, save to CSV."""
    filepath = download_tlc_data(year=2024, month=1)
    df = process_tlc_data(filepath, sample_size=50000)
    output_path = os.path.join(DATA_DIR, "real_taxi_data.csv")
    df.to_csv(output_path, index=False)
    logger.info("Saved processed data to %s", output_path)
    logger.info("Sample:\n%s", df.head(10).to_string())
    return df


if __name__ == "__main__":
    run()

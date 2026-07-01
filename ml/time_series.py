"""
Time Series Demand Forecasting using ARIMA.

Usage:
    python -m ml.time_series
"""

import pandas as pd
import numpy as np
import os
import logging
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.stattools import adfuller

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
PLOTS_DIR = os.path.join(BASE_DIR, "outputs", "plots")
RESULTS_DIR = os.path.join(BASE_DIR, "outputs", "results")


def create_hourly_demand(df):
    hours = df["hour"].value_counts().sort_index()
    np.random.seed(42)
    daily_pattern = hours.values.astype(float)
    weekly_demand = []
    for day in range(7):
        day_factor = 1.0 + 0.2 * np.sin(2 * np.pi * day / 7)
        noise = np.random.normal(1.0, 0.1, len(daily_pattern))
        weekly_demand.extend((daily_pattern * day_factor * noise).tolist())
    index = pd.date_range(start="2024-01-01", periods=len(weekly_demand), freq="h")
    return pd.Series(weekly_demand, index=index, name="demand")


def fit_arima(ts, order=(2, 1, 2), forecast_hours=48):
    train_size = len(ts) - forecast_hours
    train, test = ts[:train_size], ts[train_size:]
    model = ARIMA(train, order=order)
    fitted = model.fit()
    forecast_result = fitted.get_forecast(steps=forecast_hours)
    forecast = forecast_result.predicted_mean
    conf_int = forecast_result.conf_int(alpha=0.05)
    mae = np.mean(np.abs(test.values - forecast.values[:len(test)])) if len(test) > 0 else None
    rmse = np.sqrt(np.mean((test.values - forecast.values[:len(test)])**2)) if len(test) > 0 else None
    return {"model": fitted, "forecast": forecast, "conf_int": conf_int, "train": train, "test": test, "mae": mae, "rmse": rmse, "aic": fitted.aic, "bic": fitted.bic}


def plot_forecast(result):
    fig, axes = plt.subplots(2, 1, figsize=(16, 10))
    ax = axes[0]
    ax.plot(result["train"].index, result["train"].values, color="#22d3ee", label="Training", linewidth=1)
    ax.plot(result["test"].index, result["test"].values, color="#44ff44", label="Actual", linewidth=2)
    ax.plot(result["forecast"].index, result["forecast"].values, color="#ff4444", label="Forecast", linewidth=2, linestyle="--")
    conf = result["conf_int"]
    ax.fill_between(conf.index, conf.iloc[:, 0], conf.iloc[:, 1], color="#ff4444", alpha=0.15, label="95% CI")
    ax.set_xlabel("Time"); ax.set_ylabel("Demand"); ax.set_title("Demand Forecast - ARIMA")
    ax.legend(); ax.grid(True, alpha=0.3)

    ax = axes[1]
    fs = len(result["train"]) - 24
    ax.plot(result["train"].index[fs:], result["train"].values[fs:], color="#22d3ee", label="Recent", linewidth=2)
    ax.plot(result["test"].index, result["test"].values, color="#44ff44", label="Actual", linewidth=2)
    ax.plot(result["forecast"].index, result["forecast"].values, color="#ff4444", label="Forecast", linewidth=2, linestyle="--")
    ax.fill_between(conf.index, conf.iloc[:, 0], conf.iloc[:, 1], color="#ff4444", alpha=0.15)
    ax.set_xlabel("Time"); ax.set_ylabel("Demand"); ax.set_title("Forecast Detail")
    ax.legend(); ax.grid(True, alpha=0.3)

    fig.suptitle("Time Series Demand Forecasting", fontsize=16, fontweight="bold")
    fig.tight_layout()
    fig.savefig(os.path.join(PLOTS_DIR, "time_series_forecast.png"), dpi=150, bbox_inches="tight")
    plt.close(fig)
    logger.info("Saved forecast plot")


def run():
    real_path = os.path.join(DATA_DIR, "real_taxi_data.csv")
    synth_path = os.path.join(DATA_DIR, "synthetic_rides.csv")
    data_path = real_path if os.path.exists(real_path) else synth_path
    df = pd.read_csv(data_path)
    ts = create_hourly_demand(df)
    stat = adfuller(ts, autolag="AIC")
    logger.info("Stationarity p-value: %.4f", stat[1])
    result = fit_arima(ts)
    plot_forecast(result)
    metrics = {"mae": result["mae"], "rmse": result["rmse"], "aic": result["aic"], "bic": result["bic"]}
    pd.DataFrame([metrics]).to_csv(os.path.join(RESULTS_DIR, "time_series_results.csv"), index=False)
    print("\n" + "=" * 50)
    print("TIME SERIES RESULTS")
    print("=" * 50)
    print(f"ARIMA(2,1,2)")
    if result["mae"]: print(f"MAE:  {result['mae']:.2f}")
    if result["rmse"]: print(f"RMSE: {result['rmse']:.2f}")
    print(f"AIC:  {result['aic']:.2f}")
    print("=" * 50)
    return result


if __name__ == "__main__":
    run()

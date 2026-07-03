"""
Backtesting Framework - Compares pricing strategies on historical data.

Usage:
    python -m ml.backtester
"""

import pandas as pd
import numpy as np
import os
import logging
import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
MODELS_DIR = os.path.join(BASE_DIR, "outputs", "saved_models")
PLOTS_DIR = os.path.join(BASE_DIR, "outputs", "plots")
RESULTS_DIR = os.path.join(BASE_DIR, "outputs", "results")


def fixed_pricing(distance, hour, traffic, weather):
    return 40 + distance * 12

def simple_surge_pricing(distance, hour, traffic, weather):
    base = 40 + distance * 12
    return base * {"low": 1.0, "medium": 1.3, "high": 1.6}.get(traffic, 1.0)

def rule_based_dynamic(distance, hour, traffic, weather):
    base = 40 + distance * 12
    ts = {"low": 20, "medium": 50, "high": 90}.get(traffic, 20)
    ws = {"clear": 0, "rain": 35, "snow": 60}.get(weather, 0)
    ps = 70 if (7 <= hour <= 10 or 17 <= hour <= 21) else 0
    return base + ts + ws + ps

def ml_dynamic_pricing(distance, hour, traffic, weather, model):
    tm = {"low": 1, "medium": 2, "high": 3}
    wm = {"clear": 1, "rain": 2, "snow": 3}
    ip = 1 if 7 <= hour <= 10 or 17 <= hour <= 21 else 0
    isn = 1 if hour >= 22 or hour <= 5 else 0
    te, we = tm.get(traffic, 1), wm.get(weather, 1)
    features = pd.DataFrame([{
        "distance": distance, "hour": hour, "is_peak": ip, "is_night": isn,
        "hour_sin": np.sin(2*np.pi*hour/24), "hour_cos": np.cos(2*np.pi*hour/24),
        "traffic_encoded": te, "weather_encoded": we,
        "distance_traffic": distance*te, "distance_peak": distance*ip,
        "traffic_peak": te*ip, "weather_peak": we*ip,
        "demand_score": ip*2 + we*1.5 + te*1.2
    }])
    return float(model.predict(features)[0])


def run_backtest(df, model):
    strategies = {"Fixed": [], "Simple Surge": [], "Rule-Based Dynamic": [], "ML Dynamic": []}
    for _, row in df.iterrows():
        d, h, t, w = row["distance"], int(row["hour"]), row["traffic"], row["weather"]
        strategies["Fixed"].append(fixed_pricing(d, h, t, w))
        strategies["Simple Surge"].append(simple_surge_pricing(d, h, t, w))
        strategies["Rule-Based Dynamic"].append(rule_based_dynamic(d, h, t, w))
        strategies["ML Dynamic"].append(ml_dynamic_pricing(d, h, t, w, model))

    results = []
    for name, prices in strategies.items():
        prices = np.array(prices)
        results.append({
            "Strategy": name, "Total Revenue": np.sum(prices), "Avg Fare": np.mean(prices),
            "Std Fare": np.std(prices), "Min Fare": np.min(prices), "Max Fare": np.max(prices),
            "MAE vs Actual": np.mean(np.abs(prices - df["price"].values)),
            "Revenue Uplift vs Fixed": (np.sum(prices) - np.sum(strategies["Fixed"])) / np.sum(strategies["Fixed"]) * 100
        })
    return pd.DataFrame(results)


def plot_backtest(results_df):
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    colors = ["#666", "#ffaa00", "#ff4444", "#22d3ee"]

    ax = axes[0]
    ax.bar(results_df["Strategy"], results_df["Total Revenue"], color=colors)
    ax.set_ylabel("Total Revenue"); ax.set_title("Total Revenue by Strategy")
    ax.grid(True, alpha=0.3, axis="y"); plt.setp(ax.get_xticklabels(), rotation=15, ha="right")

    ax = axes[1]
    ax.bar(results_df["Strategy"], results_df["Avg Fare"], color=colors)
    ax.set_ylabel("Avg Fare"); ax.set_title("Average Fare by Strategy")
    ax.grid(True, alpha=0.3, axis="y"); plt.setp(ax.get_xticklabels(), rotation=15, ha="right")

    ax = axes[2]
    uplift = results_df["Revenue Uplift vs Fixed"]
    bar_colors = ["#44ff44" if u > 0 else "#ff4444" for u in uplift]
    ax.bar(results_df["Strategy"], uplift, color=bar_colors)
    ax.set_ylabel("Uplift vs Fixed (%)"); ax.set_title("Revenue Uplift")
    ax.axhline(y=0, color="white", linewidth=0.5)
    ax.grid(True, alpha=0.3, axis="y"); plt.setp(ax.get_xticklabels(), rotation=15, ha="right")

    fig.suptitle("Backtesting - Pricing Strategy Comparison", fontsize=16, fontweight="bold")
    fig.tight_layout()
    fig.savefig(os.path.join(PLOTS_DIR, "backtesting.png"), dpi=150, bbox_inches="tight")
    plt.close(fig)
    logger.info("Saved backtesting plot")


def run():
    real_path = os.path.join(DATA_DIR, "real_taxi_data.csv")
    synth_path = os.path.join(DATA_DIR, "synthetic_rides.csv")
    data_path = real_path if os.path.exists(real_path) else synth_path
    df = pd.read_csv(data_path)
    model = joblib.load(os.path.join(MODELS_DIR, "xgboost_model.pkl"))
    logger.info("Running backtest on %d rides...", len(df))
    results = run_backtest(df, model)
    plot_backtest(results)
    results.to_csv(os.path.join(RESULTS_DIR, "backtesting_results.csv"), index=False)
    print("\n" + "=" * 80)
    print("BACKTESTING RESULTS")
    print("=" * 80)
    print(results.to_string(index=False))
    print("=" * 80)
    return results


if __name__ == "__main__":
    run()

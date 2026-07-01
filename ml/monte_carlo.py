"""
Monte Carlo Simulation for Pricing Risk Assessment
Simulates N scenarios and computes revenue VaR, confidence intervals.

Usage:
    python -m ml.monte_carlo
"""

import numpy as np
import pandas as pd
import os
import logging
import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(BASE_DIR, "outputs", "saved_models")
DATA_DIR = os.path.join(BASE_DIR, "data")
PLOTS_DIR = os.path.join(BASE_DIR, "outputs", "plots")
RESULTS_DIR = os.path.join(BASE_DIR, "outputs", "results")


def create_features_array(distance, hour, traffic_encoded, weather_encoded):
    is_peak = 1 if 7 <= hour <= 10 or 17 <= hour <= 21 else 0
    is_night = 1 if hour >= 22 or hour <= 5 else 0
    return [
        distance, hour, is_peak, is_night,
        np.sin(2 * np.pi * hour / 24), np.cos(2 * np.pi * hour / 24),
        traffic_encoded, weather_encoded,
        distance * traffic_encoded, distance * is_peak,
        traffic_encoded * is_peak, weather_encoded * is_peak,
        is_peak * 2 + weather_encoded * 1.5 + traffic_encoded * 1.2
    ]


def run_simulation(n_simulations=10000, seed=42):
    np.random.seed(seed)
    model_path = os.path.join(MODELS_DIR, "xgboost_model.pkl")
    if not os.path.exists(model_path):
        logger.error("Model not found at %s", model_path)
        return None, None, None
    model = joblib.load(model_path)

    real_path = os.path.join(DATA_DIR, "real_taxi_data.csv")
    synth_path = os.path.join(DATA_DIR, "synthetic_rides.csv")
    data_path = real_path if os.path.exists(real_path) else synth_path
    df = pd.read_csv(data_path)

    traffic_map = {"low": 1, "medium": 2, "high": 3}
    weather_map = {"clear": 1, "rain": 2, "snow": 3}

    sim_distances = np.random.choice(df["distance"].values, size=n_simulations)
    sim_hours = np.random.choice(df["hour"].values, size=n_simulations)
    sim_traffic = np.random.choice(df["traffic"].map(traffic_map).values, size=n_simulations)
    sim_weather = np.random.choice(df["weather"].map(weather_map).values, size=n_simulations)

    features = [create_features_array(sim_distances[i], int(sim_hours[i]), int(sim_traffic[i]), int(sim_weather[i])) for i in range(n_simulations)]
    feature_cols = ["distance", "hour", "is_peak", "is_night", "hour_sin", "hour_cos", "traffic_encoded", "weather_encoded", "distance_traffic", "distance_peak", "traffic_peak", "weather_peak", "demand_score"]
    X_sim = pd.DataFrame(features, columns=feature_cols)

    predicted_fares = np.maximum(model.predict(X_sim), 40)
    results = {
        "mean_fare": np.mean(predicted_fares), "median_fare": np.median(predicted_fares),
        "std_fare": np.std(predicted_fares), "min_fare": np.min(predicted_fares),
        "max_fare": np.max(predicted_fares),
        "var_95": np.percentile(predicted_fares, 5), "var_99": np.percentile(predicted_fares, 1),
        "ci_lower_95": np.percentile(predicted_fares, 2.5), "ci_upper_95": np.percentile(predicted_fares, 97.5),
        "n_simulations": n_simulations
    }
    return predicted_fares, results, X_sim


def plot_simulation(fares, results):
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))

    ax = axes[0, 0]
    ax.hist(fares, bins=80, color="#22d3ee", alpha=0.7, edgecolor="none")
    ax.axvline(results["mean_fare"], color="#ff4444", linestyle="--", linewidth=2, label=f'Mean: {results["mean_fare"]:.0f}')
    ax.axvline(results["median_fare"], color="#44ff44", linestyle="--", linewidth=2, label=f'Median: {results["median_fare"]:.0f}')
    ax.set_xlabel("Predicted Fare"); ax.set_ylabel("Frequency")
    ax.set_title(f"Fare Distribution (n={results['n_simulations']:,})"); ax.legend(); ax.grid(True, alpha=0.3)

    ax = axes[0, 1]
    sorted_fares = np.sort(fares)
    ax.plot(sorted_fares, np.linspace(0, 1, len(sorted_fares)), color="#22d3ee", linewidth=2)
    ax.axhline(0.05, color="#ff4444", linestyle="--", alpha=0.8, label=f'VaR 95%: {results["var_95"]:.0f}')
    ax.axhline(0.01, color="#ff8800", linestyle="--", alpha=0.8, label=f'VaR 99%: {results["var_99"]:.0f}')
    ax.set_xlabel("Fare"); ax.set_ylabel("Cumulative Probability")
    ax.set_title("Value at Risk (VaR)"); ax.legend(); ax.grid(True, alpha=0.3)

    ax = axes[1, 0]
    ci_data = [("99% CI", results["var_99"], np.percentile(fares, 99)), ("95% CI", results["ci_lower_95"], results["ci_upper_95"]), ("Mean +/- s", results["mean_fare"] - results["std_fare"], results["mean_fare"] + results["std_fare"])]
    for i, (label, lower, upper) in enumerate(ci_data):
        ax.barh(i, upper - lower, left=lower, height=0.5, color=["#ff4444", "#22d3ee", "#44ff44"][i], alpha=0.7)
    ax.set_yticks(range(len(ci_data))); ax.set_yticklabels([c[0] for c in ci_data])
    ax.set_xlabel("Fare"); ax.set_title("Confidence Intervals"); ax.grid(True, alpha=0.3, axis="x")

    ax = axes[1, 1]
    ax.hist(fares, bins=50, color="#22d3ee", alpha=0.5, density=True)
    ax.set_xlabel("Fare"); ax.set_ylabel("Density"); ax.set_title("Fare Density"); ax.grid(True, alpha=0.3)

    fig.suptitle("Monte Carlo Simulation - Risk Assessment", fontsize=16, fontweight="bold")
    fig.tight_layout()
    fig.savefig(os.path.join(PLOTS_DIR, "monte_carlo_simulation.png"), dpi=150, bbox_inches="tight")
    plt.close(fig)
    logger.info("Saved Monte Carlo plot")


def run():
    fares, results, X_sim = run_simulation(n_simulations=10000)
    if fares is None: return
    plot_simulation(fares, results)
    pd.DataFrame([results]).to_csv(os.path.join(RESULTS_DIR, "monte_carlo_results.csv"), index=False)
    print("\n" + "=" * 60)
    print("MONTE CARLO SIMULATION RESULTS")
    print("=" * 60)
    print(f"Simulations:     {results['n_simulations']:,}")
    print(f"Mean Fare:       {results['mean_fare']:.2f}")
    print(f"Median Fare:     {results['median_fare']:.2f}")
    print(f"95% VaR:         {results['var_95']:.2f}")
    print(f"99% VaR:         {results['var_99']:.2f}")
    print(f"95% CI:          [{results['ci_lower_95']:.2f}, {results['ci_upper_95']:.2f}]")
    print("=" * 60)
    return fares, results


if __name__ == "__main__":
    run()

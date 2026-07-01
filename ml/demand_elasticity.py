"""
Demand Elasticity Analysis
Analyzes price sensitivity: how does demand change with price?

Usage:
    python -m ml.demand_elasticity
"""

import pandas as pd
import numpy as np
import os
import logging
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
PLOTS_DIR = os.path.join(BASE_DIR, "outputs", "plots")
RESULTS_DIR = os.path.join(BASE_DIR, "outputs", "results")


def compute_elasticity(df: pd.DataFrame, n_bins: int = 20) -> pd.DataFrame:
    df = df.copy()
    df["price_bin"] = pd.qcut(df["price"], q=n_bins, duplicates="drop")
    df["price_midpoint"] = df["price_bin"].apply(lambda x: float(x.mid))
    demand = df.groupby("price_midpoint").size().reset_index(name="demand")
    demand = demand.sort_values("price_midpoint")
    demand["price_midpoint"] = demand["price_midpoint"].astype(float)
    demand["pct_change_price"] = demand["price_midpoint"].pct_change()
    demand["pct_change_demand"] = demand["demand"].pct_change()
    demand["elasticity"] = demand["pct_change_demand"] / demand["pct_change_price"]
    demand["elasticity"] = demand["elasticity"].replace([np.inf, -np.inf], np.nan)
    return demand


def compute_conditional_elasticity(df: pd.DataFrame) -> dict:
    conditions = {
        "Peak Hours": df[df["hour"].apply(lambda h: 7 <= h <= 10 or 17 <= h <= 21)],
        "Off-Peak": df[df["hour"].apply(lambda h: not (7 <= h <= 10 or 17 <= h <= 21))],
        "Rain": df[df["weather"] == "rain"],
        "Clear": df[df["weather"] == "clear"],
        "High Traffic": df[df["traffic"] == "high"],
        "Low Traffic": df[df["traffic"] == "low"],
    }
    results = {}
    for name, subset in conditions.items():
        if len(subset) > 50:
            elast = compute_elasticity(subset)
            results[name] = elast["elasticity"].dropna().median()
    return results


def plot_elasticity(demand_df: pd.DataFrame, conditional: dict):
    fig, axes = plt.subplots(1, 3, figsize=(20, 6))
    ax = axes[0]
    ax.plot(demand_df["price_midpoint"], demand_df["demand"], "o-", color="#22d3ee", linewidth=2, markersize=4)
    ax.set_xlabel("Price")
    ax.set_ylabel("Demand (# rides)")
    ax.set_title("Demand Curve")
    ax.grid(True, alpha=0.3)

    ax = axes[1]
    valid = demand_df.dropna(subset=["elasticity"])
    colors = ["#ff4444" if e < -1 else "#44ff44" if e > -0.5 else "#ffaa00" for e in valid["elasticity"]]
    ax.bar(range(len(valid)), valid["elasticity"], color=colors)
    ax.axhline(y=-1, color="white", linestyle="--", alpha=0.5, label="Unit elastic")
    ax.set_xlabel("Price Level")
    ax.set_ylabel("Elasticity")
    ax.set_title("Price Elasticity of Demand")
    ax.legend()
    ax.grid(True, alpha=0.3)

    ax = axes[2]
    names = list(conditional.keys())
    values = list(conditional.values())
    bar_colors = ["#22d3ee" if v < 0 else "#ff4444" for v in values]
    ax.barh(names, values, color=bar_colors)
    ax.axvline(x=-1, color="white", linestyle="--", alpha=0.5)
    ax.set_xlabel("Median Elasticity")
    ax.set_title("Elasticity by Condition")
    ax.grid(True, alpha=0.3, axis="x")

    fig.suptitle("Demand Elasticity Analysis", fontsize=16, fontweight="bold")
    fig.tight_layout()
    fig.savefig(os.path.join(PLOTS_DIR, "demand_elasticity.png"), dpi=150, bbox_inches="tight")
    plt.close(fig)
    logger.info("Saved elasticity plot")


def run():
    real_path = os.path.join(DATA_DIR, "real_taxi_data.csv")
    synth_path = os.path.join(DATA_DIR, "synthetic_rides.csv")
    data_path = real_path if os.path.exists(real_path) else synth_path
    df = pd.read_csv(data_path)
    logger.info("Loaded %d rides", len(df))

    demand = compute_elasticity(df)
    overall_elasticity = demand["elasticity"].dropna().median()
    conditional = compute_conditional_elasticity(df)
    plot_elasticity(demand, conditional)

    results = {"overall_median_elasticity": overall_elasticity}
    results.update({f"elasticity_{k}": v for k, v in conditional.items()})
    pd.DataFrame([results]).to_csv(os.path.join(RESULTS_DIR, "elasticity_results.csv"), index=False)

    print("\n" + "=" * 50)
    print("DEMAND ELASTICITY ANALYSIS")
    print("=" * 50)
    print(f"Overall Median Elasticity: {overall_elasticity:.3f}")
    for k, v in conditional.items():
        print(f"  {k:20s}: {v:.3f}")
    print("=" * 50)
    return demand, conditional


if __name__ == "__main__":
    run()

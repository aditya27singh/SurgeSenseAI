"""
Revenue Optimization Module
Formulates: Revenue = Price * Demand(Price)
Finds optimal price using scipy.optimize.

Usage:
    python -m ml.revenue_optimizer
"""

import numpy as np
import pandas as pd
import os
import logging
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.optimize import minimize_scalar

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLOTS_DIR = os.path.join(BASE_DIR, "outputs", "plots")
RESULTS_DIR = os.path.join(BASE_DIR, "outputs", "results")


def demand_function(price, base_demand=100, elasticity=-1.2):
    P_REF = 200.0
    demand = base_demand * (price / P_REF) ** elasticity
    return max(demand, 0)


def revenue_function(price, base_demand=100, elasticity=-1.2):
    return price * demand_function(price, base_demand, elasticity)


def find_optimal_price(base_demand=100, elasticity=-1.2, price_range=(50, 2000)):
    result = minimize_scalar(lambda p: -revenue_function(p, base_demand, elasticity), bounds=price_range, method="bounded")
    return {"optimal_price": result.x, "optimal_revenue": -result.fun, "optimal_demand": demand_function(result.x, base_demand, elasticity), "base_demand": base_demand, "elasticity": elasticity}


def plot_revenue_curves():
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    prices = np.linspace(50, 1500, 200)

    ax = axes[0, 0]
    for e in [-0.5, -1.0, -1.5, -2.0]:
        revenues = [revenue_function(p, elasticity=e) for p in prices]
        ax.plot(prices, revenues, label=f"e = {e}")
        opt = find_optimal_price(elasticity=e)
        ax.plot(opt["optimal_price"], opt["optimal_revenue"], "o", markersize=8)
    ax.set_xlabel("Price"); ax.set_ylabel("Revenue"); ax.set_title("Revenue vs Price - Different Elasticities")
    ax.legend(); ax.grid(True, alpha=0.3)

    ax = axes[0, 1]
    for bd, label in [(150, "Peak Hour"), (100, "Normal"), (60, "Off-Peak")]:
        revenues = [revenue_function(p, base_demand=bd) for p in prices]
        ax.plot(prices, revenues, label=label, linewidth=2)
    ax.set_xlabel("Price"); ax.set_ylabel("Revenue"); ax.set_title("Revenue vs Price - Demand Scenarios")
    ax.legend(); ax.grid(True, alpha=0.3)

    ax = axes[1, 0]
    for e in [-0.8, -1.2, -1.8]:
        demands = [demand_function(p, elasticity=e) for p in prices]
        ax.plot(prices, demands, label=f"e = {e}")
    ax.set_xlabel("Price"); ax.set_ylabel("Demand"); ax.set_title("Demand Curves")
    ax.legend(); ax.grid(True, alpha=0.3)

    ax = axes[1, 1]
    elasticities = np.linspace(-2.5, -0.3, 50)
    optimal_prices = [find_optimal_price(elasticity=e)["optimal_price"] for e in elasticities]
    ax.plot(elasticities, optimal_prices, "o-", color="#22d3ee", markersize=3)
    ax.set_xlabel("Elasticity"); ax.set_ylabel("Optimal Price")
    ax.set_title("Optimal Price vs Elasticity"); ax.grid(True, alpha=0.3)

    fig.suptitle("Revenue Optimization Analysis", fontsize=16, fontweight="bold")
    fig.tight_layout()
    fig.savefig(os.path.join(PLOTS_DIR, "revenue_optimization.png"), dpi=150, bbox_inches="tight")
    plt.close(fig)
    logger.info("Saved revenue optimization plots")


def run():
    scenarios = [
        {"name": "Normal", "base_demand": 100, "elasticity": -1.2},
        {"name": "Peak Hour", "base_demand": 150, "elasticity": -0.8},
        {"name": "Rainy Peak", "base_demand": 180, "elasticity": -0.6},
        {"name": "Off-Peak Night", "base_demand": 50, "elasticity": -1.8},
        {"name": "Snow Storm", "base_demand": 200, "elasticity": -0.4},
    ]
    results = []
    print("\n" + "=" * 70)
    print("REVENUE OPTIMIZATION RESULTS")
    print("=" * 70)
    for s in scenarios:
        opt = find_optimal_price(base_demand=s["base_demand"], elasticity=s["elasticity"])
        opt["scenario"] = s["name"]
        results.append(opt)
        print(f"{s['name']:20s} Opt Price: {opt['optimal_price']:10.2f}  Revenue: {opt['optimal_revenue']:12.2f}")
    print("=" * 70)
    pd.DataFrame(results).to_csv(os.path.join(RESULTS_DIR, "revenue_optimization.csv"), index=False)
    plot_revenue_curves()
    return pd.DataFrame(results)


if __name__ == "__main__":
    run()

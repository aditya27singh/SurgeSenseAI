"""
Comprehensive ML Training Pipeline
Trains and evaluates multiple models with cross-validation,
ablation study, and learning curves.

Usage:
    python -m ml.train_pipeline
"""

import pandas as pd
import numpy as np
import os
import logging
import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split, KFold, learning_curve
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import (
    mean_absolute_error, mean_squared_error, r2_score,
    mean_absolute_percentage_error
)
import xgboost as xgb

try:
    import lightgbm as lgb
    HAS_LIGHTGBM = True
except ImportError:
    HAS_LIGHTGBM = False
    print("WARNING: lightgbm not installed. Skipping LightGBM model.")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")
RESULTS_DIR = os.path.join(OUTPUT_DIR, "results")
PLOTS_DIR = os.path.join(OUTPUT_DIR, "plots")
MODELS_DIR = os.path.join(OUTPUT_DIR, "saved_models")

for d in [RESULTS_DIR, PLOTS_DIR, MODELS_DIR]:
    os.makedirs(d, exist_ok=True)


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    traffic_map = {"low": 1, "medium": 2, "high": 3}
    weather_map = {"clear": 1, "rain": 2, "snow": 3}
    df["traffic_encoded"] = df["traffic"].map(traffic_map).fillna(1)
    df["weather_encoded"] = df["weather"].map(weather_map).fillna(1)
    df["is_peak"] = df["hour"].apply(lambda h: 1 if 7 <= h <= 10 or 17 <= h <= 21 else 0)
    df["is_night"] = df["hour"].apply(lambda h: 1 if h >= 22 or h <= 5 else 0)
    df["hour_sin"] = np.sin(2 * np.pi * df["hour"] / 24)
    df["hour_cos"] = np.cos(2 * np.pi * df["hour"] / 24)
    df["distance_traffic"] = df["distance"] * df["traffic_encoded"]
    df["distance_peak"] = df["distance"] * df["is_peak"]
    df["traffic_peak"] = df["traffic_encoded"] * df["is_peak"]
    df["weather_peak"] = df["weather_encoded"] * df["is_peak"]
    df["demand_score"] = df["is_peak"] * 2 + df["weather_encoded"] * 1.5 + df["traffic_encoded"] * 1.2
    return df


FEATURE_COLS = [
    "distance", "hour", "is_peak", "is_night", "hour_sin", "hour_cos",
    "traffic_encoded", "weather_encoded", "distance_traffic", "distance_peak",
    "traffic_peak", "weather_peak", "demand_score"
]
TARGET_COL = "price"


def get_models() -> dict:
    models = {
        "Linear Regression": LinearRegression(),
        "Ridge (a=1.0)": Ridge(alpha=1.0),
        "Ridge (a=10.0)": Ridge(alpha=10.0),
        "Lasso (a=0.1)": Lasso(alpha=0.1),
        "Lasso (a=1.0)": Lasso(alpha=1.0),
        "Random Forest": RandomForestRegressor(n_estimators=200, max_depth=15, min_samples_split=5, random_state=42, n_jobs=-1),
        "XGBoost": xgb.XGBRegressor(n_estimators=300, max_depth=8, learning_rate=0.05, subsample=0.8, colsample_bytree=0.8, random_state=42, verbosity=0),
    }
    if HAS_LIGHTGBM:
        models["LightGBM"] = lgb.LGBMRegressor(n_estimators=300, max_depth=8, learning_rate=0.05, subsample=0.8, colsample_bytree=0.8, random_state=42, verbose=-1)
    return models


def evaluate_model(y_true, y_pred) -> dict:
    return {
        "MAE": mean_absolute_error(y_true, y_pred),
        "RMSE": np.sqrt(mean_squared_error(y_true, y_pred)),
        "R2": r2_score(y_true, y_pred),
        "MAPE": mean_absolute_percentage_error(y_true, y_pred) * 100
    }


def cross_validate_model(model, X, y, n_folds=5):
    kf = KFold(n_splits=n_folds, shuffle=True, random_state=42)
    fold_metrics = []
    for fold, (train_idx, val_idx) in enumerate(kf.split(X), 1):
        X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
        y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]
        model_clone = type(model)(**model.get_params())
        model_clone.fit(X_train, y_train)
        y_pred = model_clone.predict(X_val)
        metrics = evaluate_model(y_val, y_pred)
        metrics["fold"] = fold
        fold_metrics.append(metrics)
    return pd.DataFrame(fold_metrics)


def plot_learning_curves(model, X, y, model_name: str):
    train_sizes, train_scores, val_scores = learning_curve(
        model, X, y, cv=5, train_sizes=np.linspace(0.1, 1.0, 10),
        scoring="neg_mean_squared_error", n_jobs=-1
    )
    train_rmse = np.sqrt(-train_scores)
    val_rmse = np.sqrt(-val_scores)
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(train_sizes, train_rmse.mean(axis=1), "o-", label="Training RMSE")
    ax.plot(train_sizes, val_rmse.mean(axis=1), "o-", label="Validation RMSE")
    ax.fill_between(train_sizes, train_rmse.mean(axis=1) - train_rmse.std(axis=1), train_rmse.mean(axis=1) + train_rmse.std(axis=1), alpha=0.15)
    ax.fill_between(train_sizes, val_rmse.mean(axis=1) - val_rmse.std(axis=1), val_rmse.mean(axis=1) + val_rmse.std(axis=1), alpha=0.15)
    ax.set_xlabel("Training Set Size")
    ax.set_ylabel("RMSE")
    ax.set_title(f"Learning Curve - {model_name}")
    ax.legend()
    ax.grid(True, alpha=0.3)
    path = os.path.join(PLOTS_DIR, f"learning_curve_{model_name.lower().replace(' ', '_')}.png")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    logger.info("Saved learning curve: %s", path)


def run_ablation_study(X_train, y_train, X_test, y_test):
    feature_groups = {
        "Time features": ["hour", "hour_sin", "hour_cos", "is_peak", "is_night"],
        "Traffic features": ["traffic_encoded", "distance_traffic", "traffic_peak"],
        "Weather features": ["weather_encoded", "weather_peak"],
        "Interaction features": ["distance_traffic", "distance_peak", "traffic_peak", "weather_peak"],
        "Demand score": ["demand_score"],
        "Distance only": ["distance"],
    }
    baseline_model = xgb.XGBRegressor(n_estimators=300, max_depth=8, learning_rate=0.05, verbosity=0)
    baseline_model.fit(X_train, y_train)
    baseline_r2 = r2_score(y_test, baseline_model.predict(X_test))
    results = [{"Feature Group": "All features (baseline)", "R2": baseline_r2, "R2 Drop": 0.0}]
    for group_name, group_features in feature_groups.items():
        cols_to_keep = [c for c in FEATURE_COLS if c not in group_features]
        if not cols_to_keep: continue
        m = xgb.XGBRegressor(n_estimators=300, max_depth=8, learning_rate=0.05, verbosity=0)
        m.fit(X_train[cols_to_keep], y_train)
        r2 = r2_score(y_test, m.predict(X_test[cols_to_keep]))
        results.append({"Feature Group": f"Without {group_name}", "R2": r2, "R2 Drop": baseline_r2 - r2})
    df = pd.DataFrame(results)
    fig, ax = plt.subplots(figsize=(10, 6))
    colors = ["#22d3ee" if r == 0 else "#ff4444" for r in df["R2 Drop"]]
    ax.barh(df["Feature Group"], df["R2"], color=colors)
    ax.set_xlabel("R2 Score")
    ax.set_title("Ablation Study - Impact of Feature Groups")
    ax.grid(True, alpha=0.3, axis="x")
    fig.savefig(os.path.join(PLOTS_DIR, "ablation_study.png"), dpi=150, bbox_inches="tight")
    plt.close(fig)
    df.to_csv(os.path.join(RESULTS_DIR, "ablation_study.csv"), index=False)
    logger.info("Ablation study saved")
    return df


def run_pipeline(data_path: str = None):
    if data_path is None:
        real_path = os.path.join(DATA_DIR, "real_taxi_data.csv")
        synth_path = os.path.join(DATA_DIR, "synthetic_rides.csv")
        data_path = real_path if os.path.exists(real_path) else synth_path

    logger.info("Loading data from %s", data_path)
    df = pd.read_csv(data_path)
    logger.info("Data shape: %s", df.shape)
    df = engineer_features(df)
    X = df[FEATURE_COLS]
    y = df[TARGET_COL]

    X_trainval, X_test, y_trainval, y_test = train_test_split(X, y, test_size=0.15, random_state=42)
    X_train, X_val, y_train, y_val = train_test_split(X_trainval, y_trainval, test_size=0.176, random_state=42)
    logger.info("Train: %d | Val: %d | Test: %d", len(X_train), len(X_val), len(X_test))

    models = get_models()
    all_results = []
    best_r2 = -float("inf")
    best_model = None
    best_model_name = None

    for name, model in models.items():
        logger.info("Training: %s", name)
        model.fit(X_train, y_train)
        y_pred_test = model.predict(X_test)
        metrics = evaluate_model(y_test, y_pred_test)
        metrics["Model"] = name
        all_results.append(metrics)
        logger.info("  %s - MAE: %.2f | RMSE: %.2f | R2: %.4f | MAPE: %.2f%%", name, metrics["MAE"], metrics["RMSE"], metrics["R2"], metrics["MAPE"])
        if metrics["R2"] > best_r2:
            best_r2 = metrics["R2"]
            best_model = model
            best_model_name = name

    results_df = pd.DataFrame(all_results)
    results_df.to_csv(os.path.join(RESULTS_DIR, "model_evaluation_results.csv"), index=False)
    logger.info("Best model: %s (R2 = %.4f)", best_model_name, best_r2)

    # Cross-validation
    logger.info("Running 5-fold CV...")
    cv_all = []
    for name in [best_model_name, "Random Forest"]:
        if name in models:
            cv_df = cross_validate_model(models[name], X_trainval, y_trainval)
            cv_df["Model"] = name
            cv_all.append(cv_df)
            logger.info("  %s - CV R2: %.4f +/- %.4f", name, cv_df["R2"].mean(), cv_df["R2"].std())
    if cv_all:
        pd.concat(cv_all).to_csv(os.path.join(RESULTS_DIR, "cv_results.csv"), index=False)

    # Learning curves
    logger.info("Generating learning curves...")
    plot_learning_curves(models[best_model_name], X_trainval, y_trainval, best_model_name)

    # Feature importance
    if hasattr(best_model, "feature_importances_"):
        importance = pd.DataFrame({"Feature": FEATURE_COLS, "Importance": best_model.feature_importances_}).sort_values("Importance", ascending=False)
        importance.to_csv(os.path.join(RESULTS_DIR, "xgb_feature_importance.csv"), index=False)
        fig, ax = plt.subplots(figsize=(10, 8))
        ax.barh(importance["Feature"], importance["Importance"], color="#22d3ee")
        ax.set_xlabel("Importance")
        ax.set_title(f"Feature Importance - {best_model_name}")
        ax.invert_yaxis()
        ax.grid(True, alpha=0.3, axis="x")
        fig.savefig(os.path.join(PLOTS_DIR, "feature_importance.png"), dpi=150, bbox_inches="tight")
        plt.close(fig)

    # Model comparison plot
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    for ax, metric in zip(axes, ["MAE", "RMSE", "R2"]):
        colors = ["#22d3ee" if m == best_model_name else "#666" for m in results_df["Model"]]
        ax.barh(results_df["Model"], results_df[metric], color=colors)
        ax.set_xlabel(metric)
        ax.set_title(metric)
        ax.grid(True, alpha=0.3, axis="x")
    fig.suptitle("Model Comparison", fontsize=16, fontweight="bold")
    fig.tight_layout()
    fig.savefig(os.path.join(PLOTS_DIR, "model_comparison.png"), dpi=150, bbox_inches="tight")
    plt.close(fig)

    # Ablation study
    logger.info("Running ablation study...")
    run_ablation_study(X_train, y_train, X_test, y_test)

    # Save best model
    model_path = os.path.join(MODELS_DIR, "xgboost_model.pkl")
    joblib.dump(best_model, model_path)
    logger.info("Saved best model to %s", model_path)

    print("\n" + "=" * 60)
    print("TRAINING PIPELINE COMPLETE")
    print("=" * 60)
    print(f"Best Model: {best_model_name}")
    print(f"Test R2:    {best_r2:.4f}")
    print(f"Results:    {RESULTS_DIR}")
    print(f"Plots:      {PLOTS_DIR}")
    print(f"Model:      {model_path}")
    print("=" * 60)
    return best_model, results_df


if __name__ == "__main__":
    run_pipeline()

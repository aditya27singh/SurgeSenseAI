import pytest
import os
import sys
import numpy as np
import joblib
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "outputs", "saved_models", "xgboost_model.pkl")


def make_features(distance=10.0, hour=12, traffic_enc=2, weather_enc=1):
    is_peak = 1 if 7 <= hour <= 10 or 17 <= hour <= 21 else 0
    is_night = 1 if hour >= 22 or hour <= 5 else 0
    return pd.DataFrame([{
        "distance": distance, "hour": hour, "is_peak": is_peak, "is_night": is_night,
        "hour_sin": np.sin(2 * np.pi * hour / 24),
        "hour_cos": np.cos(2 * np.pi * hour / 24),
        "traffic_encoded": traffic_enc, "weather_encoded": weather_enc,
        "distance_traffic": distance * traffic_enc,
        "distance_peak": distance * is_peak, "traffic_peak": traffic_enc * is_peak,
        "weather_peak": weather_enc * is_peak,
        "demand_score": is_peak * 2 + weather_enc * 1.5 + traffic_enc * 1.2
    }])


@pytest.fixture
def model():
    if not os.path.exists(MODEL_PATH):
        pytest.skip("Model file not found")
    return joblib.load(MODEL_PATH)


class TestModelLoading:
    def test_model_file_exists(self):
        assert os.path.exists(MODEL_PATH)

    def test_model_loads(self, model):
        assert model is not None

    def test_model_has_predict(self, model):
        assert hasattr(model, "predict")


class TestModelPredictions:
    def test_prediction_returns_number(self, model):
        pred = model.predict(make_features())[0]
        assert isinstance(pred, (float, np.floating))

    def test_prediction_positive(self, model):
        pred = model.predict(make_features(distance=5.0))[0]
        assert pred > 0

    def test_prediction_scales_with_distance(self, model):
        pred_short = model.predict(make_features(distance=2.0))[0]
        pred_long = model.predict(make_features(distance=30.0))[0]
        assert pred_long > pred_short

    def test_prediction_deterministic(self, model):
        pred1 = model.predict(make_features())[0]
        pred2 = model.predict(make_features())[0]
        assert pred1 == pred2

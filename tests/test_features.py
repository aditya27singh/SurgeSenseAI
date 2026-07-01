import pytest
import numpy as np
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.main import create_features


class TestFeatureEngineering:
    def test_feature_count(self):
        df = create_features(10.0, 9, "medium", "clear")
        assert df.shape[1] == 13

    def test_peak_hour_morning(self):
        for h in [7, 8, 9, 10]:
            df = create_features(10.0, h, "low", "clear")
            assert df["is_peak"].values[0] == 1

    def test_peak_hour_evening(self):
        for h in [17, 18, 19, 20, 21]:
            df = create_features(10.0, h, "low", "clear")
            assert df["is_peak"].values[0] == 1

    def test_off_peak_hours(self):
        for h in [11, 12, 13, 14, 15, 16]:
            df = create_features(10.0, h, "low", "clear")
            assert df["is_peak"].values[0] == 0

    def test_night_detection(self):
        for h in [22, 23, 0, 1, 2, 3, 4, 5]:
            df = create_features(10.0, h, "low", "clear")
            assert df["is_night"].values[0] == 1

    def test_not_night(self):
        for h in [6, 12, 18, 21]:
            df = create_features(10.0, h, "low", "clear")
            assert df["is_night"].values[0] == 0

    def test_cyclical_encoding_bounds(self):
        for h in range(24):
            df = create_features(10.0, h, "low", "clear")
            assert -1 <= df["hour_sin"].values[0] <= 1
            assert -1 <= df["hour_cos"].values[0] <= 1

    def test_traffic_encoding(self):
        assert create_features(10.0, 12, "low", "clear")["traffic_encoded"].values[0] == 1
        assert create_features(10.0, 12, "medium", "clear")["traffic_encoded"].values[0] == 2
        assert create_features(10.0, 12, "high", "clear")["traffic_encoded"].values[0] == 3

    def test_weather_encoding(self):
        assert create_features(10.0, 12, "low", "clear")["weather_encoded"].values[0] == 1
        assert create_features(10.0, 12, "low", "rain")["weather_encoded"].values[0] == 2
        assert create_features(10.0, 12, "low", "snow")["weather_encoded"].values[0] == 3

    def test_interaction_distance_traffic(self):
        df = create_features(10.0, 12, "high", "clear")
        assert df["distance_traffic"].values[0] == 10.0 * 3

    def test_demand_score(self):
        df = create_features(10.0, 9, "high", "rain")
        expected = 1 * 2 + 2 * 1.5 + 3 * 1.2
        assert abs(df["demand_score"].values[0] - expected) < 0.01

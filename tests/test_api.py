import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


class TestHomeEndpoint:
    def test_home_returns_message(self):
        response = client.get("/")
        assert response.status_code == 200
        assert "message" in response.json()


class TestHealthEndpoint:
    def test_health_returns_status(self):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "model_loaded" in data
        assert "database" in data
        assert "version" in data


class TestPredictValidation:
    def test_invalid_hour_high(self):
        response = client.post("/predict", json={
            "pickup": "Test", "drop": "Other", "city": "Delhi", "hour": 25
        })
        assert response.status_code == 422

    def test_invalid_hour_negative(self):
        response = client.post("/predict", json={
            "pickup": "Test", "drop": "Other", "city": "Delhi", "hour": -1
        })
        assert response.status_code == 422

    def test_empty_pickup(self):
        response = client.post("/predict", json={
            "pickup": "", "drop": "Other", "city": "Delhi", "hour": 10
        })
        assert response.status_code == 422

    def test_empty_drop(self):
        response = client.post("/predict", json={
            "pickup": "Test", "drop": "", "city": "Delhi", "hour": 10
        })
        assert response.status_code == 422

    def test_whitespace_only_city(self):
        response = client.post("/predict", json={
            "pickup": "Test", "drop": "Other", "city": "   ", "hour": 10
        })
        assert response.status_code == 422

    def test_missing_field(self):
        response = client.post("/predict", json={
            "pickup": "Test", "drop": "Other"
        })
        assert response.status_code == 422


class TestRideHistory:
    def test_ride_history_returns_list(self):
        response = client.get("/ride-history")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

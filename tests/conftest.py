import pytest
import sqlite3
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def mock_weather_response():
    return {"weather": [{"main": "Clear"}], "main": {"temp": 28.5}}


@pytest.fixture
def mock_geocode_response():
    return {"features": [{"geometry": {"coordinates": [77.5946, 12.9716]}}]}


@pytest.fixture
def sample_features():
    return {"distance": 10.0, "hour": 9, "traffic": "medium", "weather": "clear"}


@pytest.fixture
def temp_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    conn = sqlite3.connect(path)
    cursor = conn.cursor()
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS rides ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, "
        "pickup TEXT, drop_location TEXT, city TEXT, "
        "predicted_fare REAL, distance_km REAL, duration_minutes REAL, "
        "traffic TEXT, weather TEXT, timestamp TEXT)"
    )
    conn.commit()
    conn.close()
    yield path
    os.close(fd)
    os.unlink(path)

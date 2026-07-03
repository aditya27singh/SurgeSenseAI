"""
SurgeSense AI â€” Backend API
AI-powered dynamic pricing engine for ride-hailing services.
"""

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator
from contextlib import contextmanager
from datetime import datetime
import sqlite3
import pandas as pd
import numpy as np
import uvicorn
import requests
import joblib
import os
import logging

from dotenv import load_dotenv

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Logging Setup
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("surgesense")

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Load ENV variables
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

load_dotenv()

weather_api_key = os.getenv('OPENWEATHER_API_KEY')
ors_api_key = os.getenv('OPENROUTESERVICE_API_KEY')

logger.info("Weather API Key Loaded: %s", weather_api_key is not None)
logger.info("OpenRouteService API Key Loaded: %s", ors_api_key is not None)

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Load Trained Model
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

MODEL_PATH = os.path.join(
    BASE_DIR, "..", "outputs", "saved_models", "xgboost_model.pkl"
)

try:
    model = joblib.load(MODEL_PATH)
    model_loaded = True
    logger.info("Model loaded successfully from %s", MODEL_PATH)
except Exception as e:
    model = None
    model_loaded = False
    logger.error("Failed to load model: %s", str(e))

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Custom Exceptions
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

class ExternalAPIError(Exception):
    """Raised when an external API call fails."""
    def __init__(self, service: str, detail: str):
        self.service = service
        self.detail = detail
        super().__init__(f"{service} API error: {detail}")


class GeocodingError(Exception):
    """Raised when geocoding fails for a location."""
    def __init__(self, location: str):
        self.location = location
        super().__init__(f"Could not geocode location: {location}")

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Create FastAPI App
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

app = FastAPI(
    title="SurgeSense API",
    description=(
        "AI-powered dynamic pricing API for ride-hailing services. "
        "Provides fare estimates based on real-time traffic, weather, "
        "and historical data using XGBoost ML models."
    ),
    version="1.0.0"
)

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# CORS Middleware
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

ALLOWED_ORIGINS = [
    "https://surgesense-ai.vercel.app",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Global Exception Handler
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

@app.exception_handler(ExternalAPIError)
async def external_api_error_handler(request: Request, exc: ExternalAPIError):
    logger.error("External API error: %s - %s", exc.service, exc.detail)
    return JSONResponse(
        status_code=502,
        content={
            "error": f"{exc.service} service unavailable",
            "detail": exc.detail,
            "status_code": 502
        }
    )


@app.exception_handler(GeocodingError)
async def geocoding_error_handler(request: Request, exc: GeocodingError):
    logger.warning("Geocoding failed for: %s", exc.location)
    return JSONResponse(
        status_code=400,
        content={
            "error": "Geocoding failed",
            "detail": f"Could not find location: {exc.location}",
            "status_code": 400
        }
    )

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# SQLite Database Setup (Connection Pool Pattern)
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

DB_PATH = os.path.join(BASE_DIR, "..", "rides.db")


def get_db():
    """Yield a database connection with row factory. Closes after use."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rides (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pickup TEXT,
            drop_location TEXT,
            city TEXT,
            predicted_fare REAL,
            distance_km REAL,
            duration_minutes REAL,
            traffic TEXT,
            weather TEXT,
            timestamp TEXT
        )
    """)
    conn.commit()
    conn.close()
    logger.info("Ride history database initialized")


init_db()

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Request / Response Schemas
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

class FarePredictionRequest(BaseModel):
    pickup: str = Field(..., min_length=1, description="Pickup location name")
    drop: str = Field(..., min_length=1, description="Drop-off location name")
    city: str = Field(..., min_length=1, description="City name for weather lookup")
    hour: int = Field(..., ge=0, le=23, description="Hour of day (0-23)")

    @field_validator("pickup", "drop", "city", mode="before")
    @classmethod
    def strip_whitespace(cls, v):
        if isinstance(v, str):
            v = v.strip()
            if not v:
                raise ValueError("Field must not be empty or whitespace-only")
        return v


class FarePredictionResponse(BaseModel):
    predicted_fare: float
    distance_km: float
    estimated_duration_minutes: float
    traffic: str
    weather: str
    temperature: float
    geometry: str
    base_fare: float
    traffic_surge: float
    weather_surge: float
    peak_hour_surge: float


class RideHistoryItem(BaseModel):
    pickup: str
    drop: str
    fare: float
    traffic: str
    weather: str
    timestamp: str


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    database: str
    version: str


class ErrorResponse(BaseModel):
    error: str
    detail: str = None
    status_code: int

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Endpoints
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

@app.get("/")
def home():
    """Root endpoint - confirms API is running."""
    return {"message": "SurgeSense AI API is running."}


@app.get("/health", response_model=HealthResponse)
def health_check():
    """Detailed health check endpoint."""
    db_status = "connected"
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("SELECT 1")
        conn.close()
    except Exception:
        db_status = "disconnected"

    return HealthResponse(
        status="healthy" if model_loaded and db_status == "connected" else "degraded",
        model_loaded=model_loaded,
        database=db_status,
        version="1.0.0"
    )

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Weather Fetch Function
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def get_weather(city: str) -> dict:
    """Fetch current weather for a city from OpenWeather API."""
    url = (
        f"https://api.openweathermap.org/data/2.5/weather"
        f"?q={city}"
        f"&appid={weather_api_key}"
        f"&units=metric"
    )

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except requests.exceptions.Timeout:
        raise ExternalAPIError("OpenWeather", "Request timed out")
    except requests.exceptions.ConnectionError:
        raise ExternalAPIError("OpenWeather", "Could not connect to weather service")
    except requests.exceptions.HTTPError as e:
        raise ExternalAPIError("OpenWeather", f"HTTP {response.status_code}: {str(e)}")

    weather_data = response.json()

    if "weather" not in weather_data or "main" not in weather_data:
        raise ExternalAPIError("OpenWeather", f"Invalid response for city: {city}")

    weather_condition = weather_data["weather"][0]["main"].lower()
    temperature = weather_data["main"]["temp"]

    if weather_condition in ["rain", "drizzle", "thunderstorm"]:
        normalized_weather = "rain"
    elif weather_condition in ["snow"]:
        normalized_weather = "snow"
    else:
        normalized_weather = "clear"

    return {
        "weather": normalized_weather,
        "temperature": temperature
    }

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Route + Traffic Fetch Function
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def get_route_info(start_location: str, end_location: str) -> dict:
    """Fetch route info from OpenRouteService API."""
    geocode_url = "https://api.openrouteservice.org/geocode/search"
    headers = {"Authorization": ors_api_key}

    # Geocode start location
    try:
        start_response = requests.get(
            geocode_url, headers=headers,
            params={"text": start_location}, timeout=10
        )
        start_response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise ExternalAPIError("OpenRouteService", f"Geocoding failed: {str(e)}")

    start_data = start_response.json()
    if not start_data.get("features"):
        raise GeocodingError(start_location)

    # Geocode end location
    try:
        end_response = requests.get(
            geocode_url, headers=headers,
            params={"text": end_location}, timeout=10
        )
        end_response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise ExternalAPIError("OpenRouteService", f"Geocoding failed: {str(e)}")

    end_data = end_response.json()
    if not end_data.get("features"):
        raise GeocodingError(end_location)

    start_coords = start_data["features"][0]["geometry"]["coordinates"]
    end_coords = end_data["features"][0]["geometry"]["coordinates"]

    route_url = "https://api.openrouteservice.org/v2/directions/driving-car"
    route_headers = {
        "Authorization": ors_api_key,
        "Content-Type": "application/json"
    }
    body = {"coordinates": [start_coords, end_coords]}

    try:
        route_response = requests.post(
            route_url, json=body, headers=route_headers, timeout=15
        )
        route_response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise ExternalAPIError("OpenRouteService", f"Routing failed: {str(e)}")

    route_data = route_response.json()

    if "routes" not in route_data or not route_data["routes"]:
        raise ExternalAPIError("OpenRouteService", "No route found between locations")

    geometry = route_data["routes"][0]["geometry"]
    summary = route_data["routes"][0]["summary"]

    distance_km = summary["distance"] / 1000
    duration_minutes = summary["duration"] / 60

    # Guard against division by zero
    if duration_minutes > 0:
        average_speed = distance_km / (duration_minutes / 60)
    else:
        average_speed = 0
        logger.warning("Duration is zero for route %s -> %s", start_location, end_location)

    if average_speed > 40:
        traffic = "low"
    elif average_speed > 20:
        traffic = "medium"
    else:
        traffic = "high"

    return {
        "distance_km": distance_km,
        "duration_minutes": duration_minutes,
        "traffic": traffic,
        "geometry": geometry
    }

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Feature Generation
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def create_features(distance: float, hour: int, traffic: str, weather: str) -> pd.DataFrame:
    """Create feature DataFrame for model prediction."""

    is_peak = 1 if 7 <= hour <= 10 or 17 <= hour <= 21 else 0
    is_night = 1 if hour >= 22 or hour <= 5 else 0

    hour_sin = np.sin(2 * np.pi * hour / 24)
    hour_cos = np.cos(2 * np.pi * hour / 24)

    traffic_map = {'low': 1, 'medium': 2, 'high': 3}
    weather_map = {'clear': 1, 'rain': 2, 'snow': 3}

    traffic_encoded = traffic_map.get(traffic, 1)
    weather_encoded = weather_map.get(weather, 1)

    distance_traffic = distance * traffic_encoded
    distance_peak = distance * is_peak
    traffic_peak = traffic_encoded * is_peak
    weather_peak = weather_encoded * is_peak

    demand_score = (
        is_peak * 2 +
        weather_encoded * 1.5 +
        traffic_encoded * 1.2
    )

    features = pd.DataFrame([{
        "distance": distance,
        "hour": hour,
        "is_peak": is_peak,
        "is_night": is_night,
        "hour_sin": hour_sin,
        "hour_cos": hour_cos,
        "traffic_encoded": traffic_encoded,
        "weather_encoded": weather_encoded,
        "distance_traffic": distance_traffic,
        "distance_peak": distance_peak,
        "traffic_peak": traffic_peak,
        "weather_peak": weather_peak,
        "demand_score": demand_score
    }])

    return features

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Live Prediction Function
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def predict_fare(start_location: str, end_location: str, city: str, hour: int) -> dict:
    """Run the full prediction pipeline."""

    if not model_loaded or model is None:
        raise HTTPException(status_code=503, detail="ML model is not loaded")

    route_info = get_route_info(start_location, end_location)
    distance = route_info["distance_km"]
    traffic = route_info["traffic"]
    geometry = route_info["geometry"]
    duration_minutes = route_info["duration_minutes"]

    weather_info = get_weather(city)
    temperature = weather_info["temperature"]
    weather = weather_info["weather"]

    features = create_features(
        distance=distance, hour=hour,
        traffic=traffic, weather=weather
    )

    ml_predicted_fare = float(model.predict(features)[0])

    # Rule-based fare breakdown
    base_fare = 40
    distance_fare = distance * 12
    base_total = base_fare + distance_fare

    traffic_surge = {"low": 20, "medium": 50, "high": 90}[traffic]
    weather_surge = {"clear": 0, "rain": 35, "snow": 60}[weather]
    peak_hour_surge = 70 if (7 <= hour <= 10 or 17 <= hour <= 21) else 0

    calculated_fare = base_total + traffic_surge + weather_surge + peak_hour_surge

    # Single blend â€” ML-dominant for short rides
    if distance < 50:
        predicted_fare = calculated_fare * 0.3 + ml_predicted_fare * 0.7
    else:
        predicted_fare = calculated_fare

    predicted_fare = max(predicted_fare, base_fare)

    return {
        "predicted_fare": float(round(predicted_fare, 2)),
        "distance_km": float(round(distance, 2)),
        "estimated_duration_minutes": float(round(duration_minutes, 2)),
        "traffic": traffic,
        "weather": weather,
        "temperature": round(temperature, 1),
        "geometry": geometry,
        "base_fare": float(round(base_total, 2)),
        "traffic_surge": float(traffic_surge),
        "weather_surge": float(weather_surge),
        "peak_hour_surge": float(peak_hour_surge)
    }


# Prediction Endpoint


@app.post("/predict", response_model=FarePredictionResponse)
def predict(request: FarePredictionRequest, db=Depends(get_db)):
    """Generate an AI-powered fare prediction."""
    logger.info(
        "Prediction request: %s -> %s in %s at hour %d",
        request.pickup, request.drop, request.city, request.hour
    )

    result = predict_fare(
        start_location=request.pickup,
        end_location=request.drop,
        city=request.city,
        hour=request.hour
    )

    try:
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO rides (
                pickup, drop_location, city,
                predicted_fare, distance_km, duration_minutes,
                traffic, weather, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            request.pickup, request.drop, request.city,
            result["predicted_fare"], result["distance_km"],
            result["estimated_duration_minutes"],
            result["traffic"], result["weather"],
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))
        db.commit()
        logger.info("Ride saved to history - fare: %.2f", result["predicted_fare"])
    except Exception as e:
        logger.error("Failed to save ride history: %s", str(e))

    return result



@app.get("/ride-history", response_model=list[RideHistoryItem])
def ride_history(db=Depends(get_db)):
    """Retrieve the 5 most recent ride predictions."""
    cursor = db.cursor()
    cursor.execute("""
        SELECT pickup, drop_location, predicted_fare,
               traffic, weather, timestamp
        FROM rides
        ORDER BY id DESC
        LIMIT 5
    """)

    rides = cursor.fetchall()
    history = []
    for ride in rides:
        history.append({
            "pickup": ride["pickup"],
            "drop": ride["drop_location"],
            "fare": ride["predicted_fare"],
            "traffic": ride["traffic"],
            "weather": ride["weather"],
            "timestamp": ride["timestamp"]
        })

    return history

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Run Server
# â” € â ” € â ” € â ” € â ” € â ” € â ” € â ” € â ” € â ” € â ” € â ” € â ” € â ” € â ” € â ” € â ” € â ” € â ” € â ” € â ” € â ” € â ”

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)


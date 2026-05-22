from fastapi import FastAPI
from pydantic import BaseModel
import pandas as pd
import numpy as np
import uvicorn
import requests
import joblib
import os
from dotenv import load_dotenv


# Load ENV variables

load_dotenv()

weather_api_key = os.getenv('OPENWEATHER_API_KEY')
ors_api_key = os.getenv('OPENROUTESERVICE_API_KEY')

print("Weather API Key Loaded:", weather_api_key is not None)
print("OpenRouteService API Key Loaded:", ors_api_key is not None)

# Load Trained Model
model = joblib.load("outputs/saved_models/xgboost_model.pkl")
print("Model Loaded Successfully")

# Create FastAPI app

app = FastAPI(
    title="SurgeSense API",
    description="AI powered dynamic pricing API for ride-hailing services. Provides fare estimates based on real-time traffic, weather, and historical data.",
    version = "1.0."
)

print("FastAPI App Initialized")

# Request Schema

class FarePredictionRequest(BaseModel):
    pickup: str
    drop: str
    city: str
    hour: int

# Weather fetch function

def get_weather(city):

    url = (
        f"https://api.openweathermap.org/data/2.5/weather"
        f"?q={city}"
        f"&appid={weather_api_key}"
        f"&units=metric"
    )

    response = requests.get(url)

    weather_data = response.json()

    # Extract weather condition
    weather_condition = (
        weather_data["weather"][0]["main"].lower()
    )

    # Extract temperature
    temperature = weather_data["main"]["temp"]

    # Normalize weather
    if weather_condition in [
        "rain",
        "drizzle",
        "thunderstorm"
    ]:
        normalized_weather = "rain"

    elif weather_condition in ["snow"]:
        normalized_weather = "snow"

    else:
        normalized_weather = "clear"

    return {
        "weather": normalized_weather,
        "temperature": temperature
    }

# Route + Traffic fetch function

def get_route_info(start_location, end_location):

    geocode_url = (
        "https://api.openrouteservice.org/geocode/search"
    )

    headers = {
        "Authorization": ors_api_key
    }

    # Start location
    start_response = requests.get(
        geocode_url,
        headers=headers,
        params={"text": start_location}
    )

    start_data = start_response.json()

    # End location
    end_response = requests.get(
        geocode_url,
        headers=headers,
        params={"text": end_location}
    )

    end_data = end_response.json()

    # Extract coordinates
    start_coords = (
        start_data["features"][0]["geometry"]["coordinates"]
    )

    end_coords = (
        end_data["features"][0]["geometry"]["coordinates"]
    )


    route_url = (
        "https://api.openrouteservice.org/v2/directions/driving-car"
    )

    headers = {
        "Authorization": ors_api_key,
        "Content-Type": "application/json"
    }

    body = {
        "coordinates": [
            start_coords,
            end_coords
        ]
    }

    route_response = requests.post(
        route_url,
        json=body,
        headers=headers
    )

    route_data = route_response.json()

    geometry = route_data["routes"][0]["geometry"]
    summary = route_data["routes"][0]["summary"]

    distance_km = summary["distance"] / 1000
    duration_minutes = summary["duration"] / 60


    average_speed = (
        distance_km /
        (duration_minutes / 60)
    )

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

# FEATURE GENERATION FUNCTION

def create_features(distance, hour, traffic, weather):

    # Peak and night flags
    is_peak = 1 if 7 <= hour <= 10 or 17 <= hour <= 21 else 0
    is_night = 1 if hour >= 22 or hour <= 5 else 0

    # Cyclical hour encoding
    hour_sin = np.sin(2 * np.pi * hour / 24)
    hour_cos = np.cos(2 * np.pi * hour / 24)

    # Encoding maps
    traffic_map = {
        'low': 1,
        'medium': 2,
        'high': 3
    }

    weather_map = {
        'clear': 1,
        'rain': 2,
        'snow': 3
    }

    # Encode categorical inputs
    traffic_encoded = traffic_map[traffic]
    weather_encoded = weather_map[weather]

    # Distance transformations
    distance_squared = distance ** 2
    distance_log = np.log1p(distance)

    # Distance bucket
    if distance <= 5:
        distance_bucket = 0
    elif distance <= 12:
        distance_bucket = 1
    elif distance <= 25:
        distance_bucket = 2
    elif distance <= 35:
        distance_bucket = 3
    else:
        distance_bucket = 4

    # Interaction features
    distance_traffic = distance * traffic_encoded
    distance_peak = distance * is_peak
    traffic_peak = traffic_encoded * is_peak
    weather_peak = weather_encoded * is_peak

    # Demand score
    demand_score = (
        is_peak * 2 +
        weather_encoded * 1.5 +
        traffic_encoded * 1.2
    )

    # Create dataframe
    features = pd.DataFrame([{
        "distance": distance,
        "hour": hour,
        "is_peak": is_peak,
        "is_night": is_night,
        "hour_sin": hour_sin,
        "hour_cos": hour_cos,
        "traffic_encoded": traffic_encoded,
        "weather_encoded": weather_encoded,
        "distance_squared": distance_squared,
        "distance_log": distance_log,
        "distance_bucket": distance_bucket,
        "distance_traffic": distance_traffic,
        "distance_peak": distance_peak,
        "traffic_peak": traffic_peak,
        "weather_peak": weather_peak,
        "demand_score": demand_score
    }])

    return features

# Live Prediction Function

def predict_fare(start_location, end_location, city, hour):

    # Get route and traffic info
    route_info = get_route_info(start_location, end_location)
    distance=route_info["distance_km"]
    traffic=route_info["traffic"]
    geometry=route_info["geometry"]
    duration_minutes=route_info["duration_minutes"]

    # Get weather info (using start location city for simplicity)
    weather_info = get_weather(city)
    temperature=weather_info["temperature"]
    weather=weather_info["weather"]

    # Create features
    features = create_features(
        distance=distance,
        hour=hour,
        traffic=traffic,
        weather=weather
    )

    # Predict fare
    predicted_fare = model.predict(features)[0]

    return {
        "predicted_fare": float(round(predicted_fare, 2)),
        "distance_km": float(round(distance, 2)),
        "estimated_duration_minutes": float(round(duration_minutes, 2)),
        "traffic": traffic,
        "weather": weather,
        "geometry": geometry,
        "temperature": round(temperature, 1)
    }

# Prediction Endpoint

@app.post("/predict")

def predict(request: FarePredictionRequest):
    
    # Run live prediction
    result = predict_fare(
        start_location=request.pickup,
        end_location=request.drop,
        city=request.city,
        hour=request.hour
    )
    return result

# Run FASTAPI Server

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
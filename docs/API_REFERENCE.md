# SurgeSense AI — API Reference

## Base URL

```
Production: https://surgesense-ai.onrender.com
Local:      http://127.0.0.1:8000
```

---

## Endpoints

### `GET /` — Health Ping

Returns a simple message confirming the API is running.

**Response:**
```json
{
  "message": "SurgeSense AI API is running."
}
```

---

### `GET /health` — Detailed Health Check

Returns system health status including model loading state and database connectivity.

**Response:**
```json
{
  "status": "healthy",
  "model_loaded": true,
  "database": "connected",
  "version": "1.0.0"
}
```

| Field | Type | Description |
|---|---|---|
| `status` | string | `"healthy"` or `"degraded"` |
| `model_loaded` | bool | Whether XGBoost model is loaded |
| `database` | string | `"connected"` or `"disconnected"` |
| `version` | string | API version |

---

### `POST /predict` — AI Fare Prediction

The core endpoint. Generates an AI-powered fare prediction using real-time traffic, weather, and the trained ML model.

**Request Body:**
```json
{
  "pickup": "Connaught Place, Delhi",
  "drop": "Indira Gandhi Airport, Delhi",
  "city": "Delhi",
  "hour": 9
}
```

| Field | Type | Constraints | Description |
|---|---|---|---|
| `pickup` | string | min 1 char, not whitespace | Pickup location name |
| `drop` | string | min 1 char, not whitespace | Drop-off location name |
| `city` | string | min 1 char, not whitespace | City for weather lookup |
| `hour` | integer | 0–23 | Hour of day |

**Response (200):**
```json
{
  "predicted_fare": 487.35,
  "distance_km": 14.82,
  "estimated_duration_minutes": 32.5,
  "traffic": "medium",
  "weather": "clear",
  "temperature": 34.2,
  "geometry": "encoded_polyline_string",
  "base_fare": 217.84,
  "traffic_surge": 50.0,
  "weather_surge": 0.0,
  "peak_hour_surge": 70.0
}
```

| Field | Type | Description |
|---|---|---|
| `predicted_fare` | float | Final AI-blended fare in ₹ |
| `distance_km` | float | Route distance in kilometers |
| `estimated_duration_minutes` | float | Estimated travel time |
| `traffic` | string | `"low"`, `"medium"`, or `"high"` |
| `weather` | string | `"clear"`, `"rain"`, or `"snow"` |
| `temperature` | float | Current temperature in °C |
| `geometry` | string | Encoded polyline for map rendering |
| `base_fare` | float | Base fare (₹40 + ₹12/km) |
| `traffic_surge` | float | Traffic surge amount |
| `weather_surge` | float | Weather surge amount |
| `peak_hour_surge` | float | Peak hour surge amount |

**Error Responses:**

| Code | When | Example |
|---|---|---|
| 422 | Invalid input | `hour: 25`, empty pickup |
| 400 | Geocoding failed | Location not found |
| 502 | External API down | Weather/routing service timeout |
| 503 | Model not loaded | ML model file missing |

**cURL Example:**
```bash
curl -X POST http://127.0.0.1:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "pickup": "India Gate, Delhi",
    "drop": "Qutub Minar, Delhi",
    "city": "Delhi",
    "hour": 18
  }'
```

---

### `GET /ride-history` — Recent Predictions

Returns the 5 most recent fare predictions.

**Response (200):**
```json
[
  {
    "pickup": "Connaught Place",
    "drop": "Airport",
    "fare": 487.35,
    "traffic": "medium",
    "weather": "clear",
    "timestamp": "2024-01-15 09:30:00"
  }
]
```

| Field | Type | Description |
|---|---|---|
| `pickup` | string | Pickup location |
| `drop` | string | Drop-off location |
| `fare` | float | Predicted fare |
| `traffic` | string | Traffic condition at prediction time |
| `weather` | string | Weather condition at prediction time |
| `timestamp` | string | ISO timestamp of prediction |

---

## Error Format

All errors return a consistent JSON structure:

```json
{
  "error": "Error type description",
  "detail": "Specific error message",
  "status_code": 400
}
```

---

## Rate Limits

The API relies on external services with their own rate limits:
- **OpenWeather API**: 60 calls/minute (free tier)
- **OpenRouteService**: 40 calls/minute (free tier)

---

## Authentication

Currently no authentication required. For production deployment, implement API key authentication via the `X-API-Key` header.

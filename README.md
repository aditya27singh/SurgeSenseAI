<p align="center">
  <h1 align="center">🚖 SurgeSense AI</h1>
  <p align="center"><strong>AI-Powered Dynamic Pricing Engine for Ride-Hailing Services</strong></p>
  <p align="center">
    <img src="https://img.shields.io/badge/python-3.11-blue?style=flat-square&logo=python" />
    <img src="https://img.shields.io/badge/FastAPI-0.100+-green?style=flat-square&logo=fastapi" />
    <img src="https://img.shields.io/badge/React-18+-61DAFB?style=flat-square&logo=react" />
    <img src="https://img.shields.io/badge/XGBoost-ML-red?style=flat-square" />
    <img src="https://img.shields.io/badge/License-MIT-yellow?style=flat-square" />
  </p>
</p>

---

## 📋 Abstract

SurgeSense AI is an intelligent fare prediction system that combines **gradient-boosted machine learning models** with **traffic and weather data** to generate dynamic pricing for ride-hailing services. The system benchmarks 4 regression models on **50,000 trips from the NYC TLC Yellow Taxi dataset (January 2024)**, performs ablation studies, ARIMA demand forecasting, and strategy backtesting — deployed as a full-stack web application with FastAPI and React.

> **Best Model:** LightGBM — R² = 0.9142, MAPE = 12.24%, validated with 5-fold CV

---

### 📸 Screenshots

#### Fare Prediction
![Prediction](screenshots/prediction.png)

#### Interactive Route Map & Ride History
![Route Map](screenshots/route-map.png)

---

## ✨ Key Features

| Category | Details |
|---|---|
| **ML Pipeline** | 4 models benchmarked (Linear Regression, Random Forest, XGBoost, LightGBM) |
| **Feature Engineering** | 13 features including cyclical encoding, interaction terms, demand scoring |
| **Real-Time Data** | Live weather (OpenWeather) + routing (OpenRouteService) |
| **Validation** | 5-fold CV on all models, ablation study, learning curves, strategy backtesting |
| **Demand Forecasting** | ARIMA(2,1,2) for 48-hour hourly demand prediction |
| **Frontend** | React 18 + Vite + Leaflet maps with dark mode UI |
| **DevOps** | Docker, GitHub Actions CI/CD, pytest test suite |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    React Frontend                        │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────────┐ │
│  │Prediction│ │ Route    │ │  Fare    │ │  Sidebar   │ │
│  │  Form    │ │  Map     │ │Breakdown │ │  History   │ │
│  └────┬─────┘ └──────────┘ └──────────┘ └────────────┘ │
│       │                                                  │
└───────┼──────────────────────────────────────────────────┘
        │ HTTP/JSON
┌───────▼──────────────────────────────────────────────────┐
│                   FastAPI Backend                         │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────────┐ │
│  │ /predict │ │ /health  │ │/ride-hist│ │  Feature   │ │
│  │          │ │          │ │          │ │  Engine    │ │
│  └────┬─────┘ └──────────┘ └──────────┘ └────────────┘ │
│       │                                                  │
│  ┌────▼─────────────────────────────────────────────┐   │
│  │              XGBoost ML Model                     │   │
│  │  13 features → fare prediction → blend with       │   │
│  │  rule-based calculation (70% ML / 30% rules)      │   │
│  └───────────────────────────────────────────────────┘   │
│       │                    │                              │
│  ┌────▼────┐         ┌────▼────┐                        │
│  │OpenWeather│        │  ORS    │                        │
│  │  API     │         │  API    │                        │
│  └──────────┘         └─────────┘                        │
└──────────────────────────────────────────────────────────┘
```

---

## 🔬 Methodology

### Dataset

NYC TLC Yellow Taxi Trip Records (January 2024) — the industry standard benchmark for ride-hailing research. After cleaning and stratified sampling: **50,000 trips** with 5 raw fields (`distance`, `hour`, `weather`, `traffic`, `price`).

> **Note:** Traffic levels are derived from average trip speed. Weather is randomly assigned with realistic NYC January probabilities (55% clear, 30% rain, 15% snow) since TLC data does not include weather fields.

### Feature Engineering (13 Features)

| Feature | Type | Rationale |
|---|---|---|
| `distance` | Continuous | Primary fare driver (explains ~46% of variance alone) |
| `hour` | Discrete | Raw temporal signal |
| `hour_sin`, `hour_cos` | Cyclical | Preserves 23→0 hour proximity |
| `is_peak`, `is_night` | Binary | Temporal demand indicators |
| `traffic_encoded` | Ordinal | Speed-derived congestion level (1=low, 2=med, 3=high) |
| `weather_encoded` | Ordinal | Weather severity (1=clear, 2=rain, 3=snow) |
| `distance_traffic` | Interaction | Surge scales with distance |
| `distance_peak` | Interaction | Peak effect × distance |
| `traffic_peak` | Interaction | Compound surge |
| `weather_peak` | Interaction | Weather-peak compound |
| `demand_score` | Composite | 2×peak + 1.5×weather + 1.2×traffic |

### Models Evaluated

| Model | R² (Test) | R² (5-Fold CV) | MAE | MAPE |
|---|---|---|---|---|
| Linear Regression | 0.9002 | 0.8998 ± 0.0039 | $3.74 | 13.58% |
| Random Forest | 0.9082 | 0.9031 ± 0.0064 | $3.56 | 12.93% |
| XGBoost (deployed) | 0.8982 | 0.8966 ± 0.0077 | $3.50 | 12.36% |
| **LightGBM (best)** | **0.9142** | **0.9077 ± 0.0064** | **$3.41** | **12.24%** |

> **Deployment choice:** XGBoost is deployed in production for backend compatibility; LightGBM is the benchmark winner.

### Ablation Study

| Removed Feature Group | R² | R² Drop |
|---|---|---|
| All features (baseline) | 0.8958 | — |
| Without Distance | 0.4391 | **−0.4566** |
| Without Traffic features | 0.8860 | −0.0098 |
| Without Interaction features | 0.8859 | −0.0099 |
| Without Weather features | 0.8951 | −0.0006 |

### Strategy Backtesting

| Strategy | Avg Fare | MAE vs Actual |
|---|---|---|
| Fixed (meter fare) | $28.00 | $7.89 |
| Simple Surge (traffic multiplier) | $32.97 | $8.08 |
| Rule-Based Dynamic (surcharges) | $34.18 | $7.39 |
| **ML Dynamic (XGBoost)** | **$28.05** | **$3.04** |

ML pricing is **2.4× more accurate** than the best rule-based approach.

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Python 3.11, FastAPI, Pydantic |
| **ML** | XGBoost, LightGBM, Scikit-learn, Statsmodels |
| **Frontend** | React 18, Vite, Leaflet, CSS |
| **Database** | SQLite |
| **APIs** | OpenWeather, OpenRouteService |
| **DevOps** | Docker, GitHub Actions |
| **Testing** | pytest |

---

## 📁 Project Structure

```
dynamic_pricing/
├── backend/
│   └── main.py                 # FastAPI backend (API, features, prediction)
├── ml/
│   ├── data_loader.py          # NYC TLC data download & processing
│   ├── train_pipeline.py       # Multi-model training + CV + ablation
│   ├── pricing_strategy.py     # Backtesting framework (4 strategies)
│   └── time_series.py          # ARIMA demand forecasting
├── frontend/
│   └── src/
│       ├── App.jsx             # Main React app component
│       ├── App.css             # Styling
│       └── main.jsx            # Entry point
├── notebooks/
│   └── analysis.ipynb          # Full analysis notebook (9 sections)
├── tests/
│   ├── test_features.py        # Feature engineering tests
│   ├── test_api.py             # API endpoint tests
│   └── test_model.py           # Model prediction tests
├── data/                       # Training data (NYC TLC)
├── outputs/
│   ├── saved_models/           # Trained XGBoost model (.pkl)
│   ├── results/                # CSV evaluation results
│   └── plots/                  # Generated analysis plots
├── docs/
│   └── API_REFERENCE.md        # API documentation
├── screenshots/                # App screenshots
├── Dockerfile                  # Backend container
├── docker-compose.yml          # Full-stack deployment
├── .github/workflows/          # CI/CD pipeline
├── requirements.txt            # Python dependencies
└── README.md
```

---

## 🚀 Quick Start

### Option 1: Docker (Recommended)

```bash
git clone https://github.com/yourusername/dynamic-pricing.git
cd dynamic-pricing
cp .env.example .env
# Add your API keys to .env

docker-compose up --build
```

### Option 2: Manual Setup

**Backend:**
```bash
pip install -r requirements.txt
cd backend && uvicorn main:app --reload
```

**Frontend:**
```bash
cd frontend && npm install && npm run dev
```

---

## 🤖 ML Pipeline Commands

```bash
# Step 1: Download and process NYC taxi data
python -m ml.data_loader

# Step 2: Train all models + CV + ablation + learning curves
python -m ml.train_pipeline

# Step 3: Run ARIMA demand forecasting
python -m ml.time_series

# Step 4: Backtest pricing strategies
python -m ml.pricing_strategy
```

---

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Individual test suites
pytest tests/test_features.py -v    # Feature engineering
pytest tests/test_api.py -v         # API endpoints
pytest tests/test_model.py -v       # Model predictions
```

---

## 🔮 Future Work

- [ ] Reinforcement learning for adaptive pricing
- [ ] Graph Neural Networks for spatial demand modeling
- [ ] Real-time traffic API integration (Google Maps, TomTom)
- [ ] Multi-city transfer learning
- [ ] Fairness constraints in pricing optimization

---

## 👤 Author

**Aditya Singh** — B.Tech Student

---

## 📄 License

This project is licensed under the MIT License — see [LICENSE](LICENSE) for details.

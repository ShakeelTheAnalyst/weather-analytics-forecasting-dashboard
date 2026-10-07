# Configuration for Real-Time Weather Analytics & Forecasting Dashboard

import os
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
MODELS_DIR = BASE_DIR / "models"
POWERBI_DIR = BASE_DIR / "powerbi"

for folder in [DATA_DIR, RAW_DATA_DIR, PROCESSED_DATA_DIR, MODELS_DIR, POWERBI_DIR]:
    folder.mkdir(parents=True, exist_ok=True)

# OpenWeatherMap API Configuration
# Sign up free at https://openweathermap.org/api to get your API key
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")
OPENWEATHER_BASE_URL = "https://api.openweathermap.org/data/2.5"

# Monitored Global Metropolises
MONITORED_CITIES = [
    {"city": "New York", "country": "USA", "lat": 40.7128, "lon": -74.0060, "region": "North America"},
    {"city": "London", "country": "UK", "lat": 51.5074, "lon": -0.1278, "region": "Europe"},
    {"city": "Tokyo", "country": "Japan", "lat": 35.6762, "lon": 139.6503, "region": "Asia-Pacific"},
    {"city": "Paris", "country": "France", "lat": 48.8566, "lon": 2.3522, "region": "Europe"},
    {"city": "Sydney", "country": "Australia", "lat": -33.8688, "lon": 151.2093, "region": "Oceania"},
    {"city": "Dubai", "country": "UAE", "lat": 25.2048, "lon": 55.2708, "region": "Middle East"},
    {"city": "Singapore", "country": "Singapore", "lat": 1.3521, "lon": 103.8198, "region": "Asia-Pacific"},
    {"city": "Mumbai", "country": "India", "lat": 19.0760, "lon": 72.8777, "region": "Asia-Pacific"},
    {"city": "Toronto", "country": "Canada", "lat": 43.6532, "lon": -79.3832, "region": "North America"},
    {"city": "Berlin", "country": "Germany", "lat": 52.5200, "lon": 13.4050, "region": "Europe"},
    {"city": "São Paulo", "country": "Brazil", "lat": -23.5505, "lon": -46.6333, "region": "South America"},
    {"city": "Cape Town", "country": "South Africa", "lat": -33.9249, "lon": 18.4241, "region": "Africa"}
]

# Random Forest Model Parameters
MODEL_HYPERPARAMETERS = {
    "n_estimators": 120,
    "max_depth": 14,
    "min_samples_split": 4,
    "min_samples_leaf": 2,
    "random_state": 42,
    "n_jobs": -1
}

# Anomaly Thresholds
ANOMALY_ZSCORE_THRESHOLD = 2.5

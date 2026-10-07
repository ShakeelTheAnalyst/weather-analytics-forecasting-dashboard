"""
API Ingestion Pipeline
Fetches real-time weather streams from OpenWeatherMap API with a robust
mathematical simulation fallback to support instant testing without API keys.
"""

import os
import time
import math
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import requests
import pandas as pd
import numpy as np

from config import (
    OPENWEATHER_API_KEY,
    OPENWEATHER_BASE_URL,
    MONITORED_CITIES,
    RAW_DATA_DIR,
    PROCESSED_DATA_DIR,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class WeatherDataPipeline:
    """End-to-end meteorological data ingestion and processing pipeline."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or OPENWEATHER_API_KEY or os.getenv("OPENWEATHER_API_KEY", "")
        self.base_url = OPENWEATHER_BASE_URL
        self.cities = MONITORED_CITIES

    def fetch_current_weather(self, city_name: str) -> Optional[Dict]:
        """Fetch real-time weather from OpenWeatherMap API."""
        if not self.api_key:
            return None

        url = f"{self.base_url}/weather"
        params = {"q": city_name, "appid": self.api_key, "units": "metric"}

        try:
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Successfully fetched live data for {city_name}")
                return {
                    "city": data["name"],
                    "country": data["sys"]["country"],
                    "timestamp": datetime.fromtimestamp(data["dt"]),
                    "temperature": data["main"]["temp"],
                    "feels_like": data["main"]["feels_like"],
                    "temp_min": data["main"]["temp_min"],
                    "temp_max": data["main"]["temp_max"],
                    "pressure": data["main"]["pressure"],
                    "humidity": data["main"]["humidity"],
                    "wind_speed": data["wind"]["speed"],
                    "wind_deg": data["wind"].get("deg", 0),
                    "cloudiness": data["clouds"]["all"],
                    "weather_main": data["weather"][0]["main"],
                    "weather_desc": data["weather"][0]["description"],
                    "visibility_km": data.get("visibility", 10000) / 1000.0,
                }
            else:
                logger.warning(f"API request for {city_name} returned code {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Error fetching data for {city_name}: {e}")
            return None

    def fetch_all_current_weather(self) -> pd.DataFrame:
        """Fetch current weather for all configured cities, falling back to simulated data if API key is missing."""
        records = []
        is_live = bool(self.api_key)

        for city_info in self.cities:
            city_name = city_info["city"]
            data = self.fetch_current_weather(city_name) if is_live else None

            if not data:
                # High-fidelity realistic simulation based on city latitude and current hour
                data = self._generate_synthetic_point(city_info, datetime.now())

            records.append(data)

        df = pd.DataFrame(records)
        raw_path = RAW_DATA_DIR / f"current_weather_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df.to_csv(raw_path, index=False)
        return df

    def _generate_synthetic_point(self, city_info: Dict, dt: datetime, is_anomaly: bool = False) -> Dict:
        """
        Generate physically consistent weather data based on latitude, diurnal solar cycle,
        seasonal progression, and microclimatic variance.
        """
        lat = city_info["lat"]
        day_of_year = dt.timetuple().tm_yday
        hour = dt.hour + (dt.minute / 60.0)

        # Baseline mean annual temperature roughly based on latitude (Equator ~ 27C, Poles ~ -15C)
        lat_effect = 28.0 - (0.55 * abs(lat))
        
        # Seasonal cycle (Northern vs Southern Hemisphere phase inversion)
        hemisphere_factor = 1.0 if lat >= 0 else -1.0
        seasonal_amplitude = 12.0 * (abs(lat) / 50.0)
        seasonal_temp = seasonal_amplitude * math.cos(2 * math.pi * (day_of_year - 200) / 365.25) * hemisphere_factor

        # Diurnal (day/night) solar curve peaking around 14:30
        diurnal_amplitude = 4.5 + (abs(lat) / 15.0)
        diurnal_temp = diurnal_amplitude * math.sin(2 * math.pi * (hour - 8.5) / 24.0)

        # Stochastic noise
        noise = np.random.normal(0, 1.2)
        temperature = lat_effect + seasonal_temp + diurnal_temp + noise

        # Inject deliberate statistical anomaly if requested
        if is_anomaly:
            anomaly_boost = np.random.choice([-8.5, 9.5])
            temperature += anomaly_boost

        humidity = np.clip(70 - (temperature * 1.1) + np.random.normal(0, 5), 20, 98)
        pressure = np.clip(1013.25 - (temperature * 0.3) + np.random.normal(0, 3.5), 980, 1035)
        wind_speed = np.clip(np.random.gamma(shape=2.5, scale=1.5), 0.5, 25.0)
        wind_deg = int(np.random.uniform(0, 360))
        cloudiness = int(np.clip(humidity * 0.9 + np.random.normal(0, 10), 0, 100))

        # Weather classification
        if cloudiness < 20:
            weather_main = "Clear"
            weather_desc = "clear sky"
        elif cloudiness < 60:
            weather_main = "Clouds"
            weather_desc = "scattered clouds"
        elif humidity > 85 and np.random.rand() > 0.4:
            weather_main = "Rain"
            weather_desc = "moderate rain" if temperature > 2 else "snow"
        else:
            weather_main = "Clouds"
            weather_desc = "overcast clouds"

        # Feels like formula approximation
        feels_like = temperature + (0.33 * (humidity / 100.0) * 6.105 * math.exp((17.27 * temperature) / (237.7 + temperature))) - (0.7 * wind_speed) - 4.0

        return {
            "city": city_info["city"],
            "country": city_info["country"],
            "region": city_info["region"],
            "latitude": lat,
            "longitude": city_info["lon"],
            "timestamp": dt,
            "temperature": round(temperature, 2),
            "feels_like": round(feels_like, 2),
            "temp_min": round(temperature - np.random.uniform(1.0, 3.0), 2),
            "temp_max": round(temperature + np.random.uniform(1.0, 3.0), 2),
            "pressure": round(pressure, 1),
            "humidity": round(humidity, 1),
            "wind_speed": round(wind_speed, 2),
            "wind_deg": wind_deg,
            "cloudiness": cloudiness,
            "weather_main": weather_main,
            "weather_desc": weather_desc,
            "visibility_km": round(np.clip(12.0 - (humidity * 0.05), 1.0, 15.0), 1),
        }

    def generate_historical_dataset(self, days: int = 90, sample_interval_hours: int = 3) -> pd.DataFrame:
        """
        Generates comprehensive multi-city historical time series dataset
        featuring realistic weather dynamics, microclimates, and labeled climate anomalies.
        """
        logger.info(f"Generating historical meteorological dataset across {len(self.cities)} cities for {days} days...")
        end_time = datetime.now().replace(minute=0, second=0, microsecond=0)
        start_time = end_time - timedelta(days=days)

        records = []
        total_steps = int((days * 24) / sample_interval_hours)

        for city_info in self.cities:
            current_time = start_time
            # Pre-determine ~2% anomalous spikes for anomaly detection testing
            anomaly_steps = set(np.random.choice(range(total_steps), size=int(total_steps * 0.025), replace=False))

            for step_idx in range(total_steps):
                is_anom = step_idx in anomaly_steps
                record = self._generate_synthetic_point(city_info, current_time, is_anomaly=is_anom)
                records.append(record)
                current_time += timedelta(hours=sample_interval_hours)

        df = pd.DataFrame(records)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df = df.sort_values(by=["city", "timestamp"]).reset_index(drop=True)

        # Save to processed directory
        historical_file = PROCESSED_DATA_DIR / "historical_weather_dataset.csv"
        df.to_csv(historical_file, index=False)
        logger.info(f"Saved {len(df):,} meteorological observations to {historical_file}")
        return df


if __name__ == "__main__":
    pipeline = WeatherDataPipeline()
    print("Testing pipeline...")
    current_df = pipeline.fetch_all_current_weather()
    print(f"Current weather sampled: {len(current_df)} cities")
    hist_df = pipeline.generate_historical_dataset(days=30, sample_interval_hours=4)
    print(f"Historical dataset created: {hist_df.shape}")

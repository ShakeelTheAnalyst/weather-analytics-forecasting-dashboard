"""
Power BI Data Exporter & Dimensional Modeling Engine
Transforms raw meteorological observations and ML forecasting inferences into
a production-grade Star Schema architecture optimized for Power BI Desktop & Service.
Generates:
  - Dim_City.csv
  - Dim_Date.csv
  - Fact_Weather_Observations.csv
  - Fact_Weather_Forecasts.csv
"""

import logging
from pathlib import Path
from typing import Dict, List
import pandas as pd
import numpy as np

from config import PROCESSED_DATA_DIR, MONITORED_CITIES

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

CLIMATE_ZONE_MAPPING = {
    "New York": "Humid Continental",
    "London": "Temperate Oceanic",
    "Tokyo": "Humid Subtropical",
    "Paris": "Oceanic",
    "Sydney": "Humid Subtropical",
    "Dubai": "Hot Arid / Desert",
    "Singapore": "Tropical Rainforest",
    "Mumbai": "Tropical Wet and Dry",
    "Toronto": "Humid Continental",
    "Berlin": "Temperate Oceanic",
    "São Paulo": "Humid Subtropical",
    "Cape Town": "Mediterranean",
}

CITY_POPULATION_EST = {
    "New York": 8336000,
    "London": 8982000,
    "Tokyo": 13960000,
    "Paris": 2161000,
    "Sydney": 5312000,
    "Dubai": 3331000,
    "Singapore": 5686000,
    "Mumbai": 12480000,
    "Toronto": 2794000,
    "Berlin": 3645000,
    "São Paulo": 12330000,
    "Cape Town": 4618000,
}


class PowerBIDataExporter:
    """Transforms raw & predicted meteorological records into a star schema for Power BI."""

    def __init__(self, output_dir: Path = PROCESSED_DATA_DIR):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_dim_city(self) -> pd.DataFrame:
        """Creates Dim_City dimension table."""
        cities_records = []
        for idx, city in enumerate(MONITORED_CITIES, start=1):
            name = city["city"]
            cities_records.append({
                "CityKey": idx,
                "CityName": name,
                "Country": city["country"],
                "Region": city["region"],
                "Latitude": city["lat"],
                "Longitude": city["lon"],
                "Coordinates": f"{city['lat']},{city['lon']}",
                "ClimateZone": CLIMATE_ZONE_MAPPING.get(name, "Temperate"),
                "Population": CITY_POPULATION_EST.get(name, 1000000),
            })
        dim_city = pd.DataFrame(cities_records)
        out_path = self.output_dir / "dim_city.csv"
        dim_city.to_csv(out_path, index=False)
        logger.info(f"Generated Dim_City ({len(dim_city)} records) -> {out_path}")
        return dim_city

    def generate_dim_date(self, start_date: str, end_date: str) -> pd.DataFrame:
        """Creates standard Power BI Dim_Date dimension table."""
        date_range = pd.date_range(start=start_date, end=end_date, freq="D")
        dates_records = []

        for d in date_range:
            month = d.month
            # Meteorological season (Northern Hemisphere general)
            if month in [12, 1, 2]:
                season = "Winter"
            elif month in [3, 4, 5]:
                season = "Spring"
            elif month in [6, 7, 8]:
                season = "Summer"
            else:
                season = "Autumn"

            dates_records.append({
                "DateKey": int(d.strftime("%Y%m%d")),
                "Date": d.strftime("%Y-%m-%d"),
                "Year": d.year,
                "Quarter": f"Q{d.quarter}",
                "QuarterYear": f"Q{d.quarter} {d.year}",
                "MonthNum": month,
                "MonthName": d.strftime("%B"),
                "MonthShort": d.strftime("%b"),
                "MonthYear": d.strftime("%b %Y"),
                "DayOfMonth": d.day,
                "DayOfWeek": d.dayofweek + 1,  # 1=Mon, 7=Sun
                "DayOfWeekName": d.strftime("%A"),
                "IsWeekend": "Yes" if d.dayofweek >= 5 else "No",
                "Season": season,
            })

        dim_date = pd.DataFrame(dates_records)
        out_path = self.output_dir / "dim_date.csv"
        dim_date.to_csv(out_path, index=False)
        logger.info(f"Generated Dim_Date ({len(dim_date)} records) -> {out_path}")
        return dim_date

    def generate_fact_observations(self, observed_df: pd.DataFrame, dim_city: pd.DataFrame) -> pd.DataFrame:
        """Transforms observed weather dataset into Fact_Weather_Observations table."""
        df = observed_df.copy()
        df["timestamp"] = pd.to_datetime(df["timestamp"])

        city_key_map = dict(zip(dim_city["CityName"], dim_city["CityKey"]))
        df["CityKey"] = df["city"].map(city_key_map)
        df["DateKey"] = df["timestamp"].dt.strftime("%Y%m%d").astype(int)

        # Standardize columns and units
        df["ObservationID"] = range(100001, 100001 + len(df))
        df["Temperature_C"] = df["temperature"].round(2)
        df["Temperature_F"] = ((df["temperature"] * 9 / 5) + 32).round(2)
        df["FeelsLike_C"] = df["feels_like"].round(2)
        df["Temp_Min_C"] = df["temp_min"].round(2)
        df["Temp_Max_C"] = df["temp_max"].round(2)
        df["Humidity_Pct"] = df["humidity"].round(1)
        df["Pressure_hPa"] = df["pressure"].round(1)
        df["WindSpeed_mps"] = df["wind_speed"].round(2)
        df["WindDirection_deg"] = df["wind_deg"].astype(int)
        df["Cloudiness_Pct"] = df["cloudiness"].astype(int)
        df["WeatherCondition"] = df["weather_main"]
        df["WeatherDescription"] = df["weather_desc"]
        df["Visibility_km"] = df["visibility_km"].round(1)

        # Statistical indices
        df["HeatIndex_C"] = df["heat_index"].round(2) if "heat_index" in df.columns else df["temperature"].round(2)
        df["VPD_kPa"] = df["vpd_kpa"].round(3) if "vpd_kpa" in df.columns else 0.0
        df["Is_Anomaly"] = df["is_anomaly"].astype(bool) if "is_anomaly" in df.columns else False
        df["Anomaly_Severity"] = df["anomaly_severity"] if "anomaly_severity" in df.columns else "Normal"
        df["Anomaly_Reason"] = df["anomaly_reason"] if "anomaly_reason" in df.columns else "Normal Conditions"
        df["Z_Score"] = df["temp_zscore"].round(2) if "temp_zscore" in df.columns else 0.0
        df["Pressure_Delta_3h"] = df["pressure_delta_3h"].round(2) if "pressure_delta_3h" in df.columns else 0.0

        fact_cols = [
            "ObservationID", "CityKey", "DateKey", "timestamp",
            "Temperature_C", "Temperature_F", "FeelsLike_C", "Temp_Min_C", "Temp_Max_C",
            "Humidity_Pct", "Pressure_hPa", "WindSpeed_mps", "WindDirection_deg",
            "Cloudiness_Pct", "WeatherCondition", "WeatherDescription", "Visibility_km",
            "HeatIndex_C", "VPD_kPa", "Is_Anomaly", "Anomaly_Severity", "Anomaly_Reason",
            "Z_Score", "Pressure_Delta_3h"
        ]

        fact_df = df[fact_cols].rename(columns={"timestamp": "ObservationTimestamp"})
        out_path = self.output_dir / "fact_weather_observations.csv"
        fact_df.to_csv(out_path, index=False)
        logger.info(f"Generated Fact_Weather_Observations ({len(fact_df):,} records) -> {out_path}")
        return fact_df

    def generate_fact_forecasts(self, forecast_records: List[Dict], dim_city: pd.DataFrame) -> pd.DataFrame:
        """Creates Fact_Weather_Forecasts table with predictions and accuracy residuals."""
        df = pd.DataFrame(forecast_records)
        df["forecast_timestamp"] = pd.to_datetime(df["forecast_timestamp"])

        city_key_map = dict(zip(dim_city["CityName"], dim_city["CityKey"]))
        df["CityKey"] = df["city"].map(city_key_map)
        df["DateKey"] = df["forecast_timestamp"].dt.strftime("%Y%m%d").astype(int)

        df["ForecastID"] = range(500001, 500001 + len(df))
        df["Horizon_Hours"] = df["horizon_hours"].astype(int)
        df["Predicted_Temp_C"] = df["predicted_temp"].round(2)
        df["Lower_Bound_C"] = df["lower_bound"].round(2)
        df["Upper_Bound_C"] = df["upper_bound"].round(2)
        df["Predicted_Humidity_Pct"] = df["predicted_humidity"].round(1)
        df["Model_Confidence_Pct"] = df["model_confidence"].round(1)

        # If actual comparison available
        if "actual_temp" in df.columns:
            df["Actual_Temp_C"] = df["actual_temp"].round(2)
            df["Residual_Error_C"] = (df["Predicted_Temp_C"] - df["Actual_Temp_C"]).round(2)
            abs_err = (df["Predicted_Temp_C"] - df["Actual_Temp_C"]).abs()
            df["Forecast_Accuracy_Pct"] = np.maximum(0, 100 - (abs_err / np.maximum(df["Actual_Temp_C"].abs(), 1.0) * 100)).round(1)
        else:
            df["Actual_Temp_C"] = np.nan
            df["Residual_Error_C"] = np.nan
            df["Forecast_Accuracy_Pct"] = df["Model_Confidence_Pct"]

        cols = [
            "ForecastID", "CityKey", "DateKey", "forecast_timestamp", "Horizon_Hours",
            "Predicted_Temp_C", "Lower_Bound_C", "Upper_Bound_C",
            "Predicted_Humidity_Pct", "Model_Confidence_Pct",
            "Actual_Temp_C", "Residual_Error_C", "Forecast_Accuracy_Pct"
        ]

        fact_forecasts = df[cols].rename(columns={"forecast_timestamp": "ForecastTimestamp"})
        out_path = self.output_dir / "fact_weather_forecasts.csv"
        fact_forecasts.to_csv(out_path, index=False)
        logger.info(f"Generated Fact_Weather_Forecasts ({len(fact_forecasts):,} records) -> {out_path}")
        return fact_forecasts

"""
Exploratory Data Analysis (EDA) & Automated Anomaly Detection Engine
Performs statistical feature engineering, anomaly detection (Z-Score & IQR),
and computes meteorological indices (Heat Index, Barometric Pressure Deltas).
"""

import math
import logging
from typing import Dict, Tuple
import pandas as pd
import numpy as np

from config import ANOMALY_ZSCORE_THRESHOLD

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class WeatherEDAProcessor:
    """Processes raw weather streams, performs EDA, and flags climate anomalies."""

    def __init__(self, z_threshold: float = ANOMALY_ZSCORE_THRESHOLD):
        self.z_threshold = z_threshold

    @staticmethod
    def calculate_heat_index(temp_c: float, humidity: float) -> float:
        """
        Calculate Steadman's Heat Index (Feels Like in heat conditions).
        Converts Celsius to Fahrenheit, applies NOAA equation, then converts back.
        """
        if temp_c < 20.0 or humidity < 40.0:
            return temp_c

        t = (temp_c * 9 / 5) + 32
        r = humidity

        # Rothfusz regression equation
        hi = (
            -42.379
            + 2.04901523 * t
            + 10.14333127 * r
            - 0.22475541 * t * r
            - 0.00683783 * (t ** 2)
            - 0.05481717 * (r ** 2)
            + 0.00122874 * (t ** 2) * r
            + 0.00085282 * t * (r ** 2)
            - 0.00000199 * (t ** 2) * (r ** 2)
        )
        hi_c = (hi - 32) * 5 / 9
        return round(hi_c, 2)

    def detect_anomalies(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Applies multi-criteria statistical anomaly detection per city:
        1. Z-score on temperature residual against local seasonal/hour baseline.
        2. Rapid Barometric Pressure Drop (indicator of abrupt weather storms).
        3. Extreme humidity-temperature discordance.
        """
        df = df.copy()
        if "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            df = df.sort_values(by=["city", "timestamp"]).reset_index(drop=True)

        df["is_anomaly"] = False
        df["anomaly_score"] = 0.0
        df["anomaly_severity"] = "Normal"
        df["anomaly_reason"] = "Normal Conditions"

        # Group by city to calculate localized baselines
        cities = df["city"].unique()
        processed_dfs = []

        for city in cities:
            cdf = df[df["city"] == city].copy()
            cdf = cdf.sort_values("timestamp")

            # Compute diurnal climatological mean by hour of day for this city
            hourly_mean = cdf.groupby(cdf["timestamp"].dt.hour)["temperature"].transform("mean")
            hourly_std = cdf.groupby(cdf["timestamp"].dt.hour)["temperature"].transform("std").fillna(1.8)
            hourly_std = hourly_std.replace(0, 1.8)

            # Residual Z-score (deviation from normal temperature at this hour of day)
            residuals = cdf["temperature"] - hourly_mean
            cdf["temp_zscore"] = (residuals / hourly_std).fillna(0.0)

            # Rapid pressure change (Storm / Front indicator)
            pressure_delta_3h = cdf["pressure"].diff().fillna(0.0)
            cdf["pressure_delta_3h"] = pressure_delta_3h

            # IQR on hourly residuals
            q25 = residuals.quantile(0.25)
            q75 = residuals.quantile(0.75)
            iqr = q75 - q25
            lower_iqr = q25 - 2.5 * iqr
            upper_iqr = q75 + 2.5 * iqr

            # Flag conditions: extreme Z-score (>= 2.8) or rapid barometric plummet (<= -6.0 hPa in 3h)
            z_anomaly = cdf["temp_zscore"].abs() >= 2.8
            iqr_anomaly = (residuals < lower_iqr) | (residuals > upper_iqr)
            pressure_storm = cdf["pressure_delta_3h"] <= -6.0

            cdf["is_anomaly"] = z_anomaly | iqr_anomaly | pressure_storm
            cdf["anomaly_score"] = cdf["temp_zscore"].abs()

            # Classify severity
            conditions = [
                (cdf["anomaly_score"] >= 3.5) | (cdf["pressure_delta_3h"] <= -8.0),
                (cdf["anomaly_score"] >= 2.8) | pressure_storm,
            ]
            choices = ["Severe Anomaly", "Moderate Warning"]
            cdf["anomaly_severity"] = np.select(conditions, choices, default="Normal")

            # Reason
            reasons = []
            for idx, row in cdf.iterrows():
                if row["anomaly_severity"] == "Normal":
                    reasons.append("Normal atmospheric range")
                elif row["pressure_delta_3h"] <= -6.0:
                    reasons.append("Rapid barometric plunge (Severe Storm Front)")
                elif row["temp_zscore"] >= 2.8:
                    reasons.append(f"Extreme heat spike (+{row['temp_zscore']:.1f}σ climatological anomaly)")
                elif row["temp_zscore"] <= -2.8:
                    reasons.append(f"Extreme cold plunge ({row['temp_zscore']:.1f}σ climatological anomaly)")
                else:
                    reasons.append("Statistical microclimate anomaly")
            cdf["anomaly_reason"] = reasons

            # Add Heat Index and Vapor Pressure Deficit
            cdf["heat_index"] = cdf.apply(lambda r: self.calculate_heat_index(r["temperature"], r["humidity"]), axis=1)
            es = 0.61078 * np.exp((17.27 * cdf["temperature"]) / (cdf["temperature"] + 237.3))
            ea = es * (cdf["humidity"] / 100.0)
            cdf["vpd_kpa"] = np.maximum(0, es - ea)

            processed_dfs.append(cdf)

        result_df = pd.concat(processed_dfs, ignore_index=True)
        return result_df

    def engineer_ml_features(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, list]:
        """
        Creates temporal, cyclical, lagged, and atmospheric interaction features
        ready for Random Forest training and forecasting.
        """
        df = df.copy()
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df = df.sort_values(by=["city", "timestamp"]).reset_index(drop=True)

        # 1. Temporal & Cyclical Features
        df["hour"] = df["timestamp"].dt.hour
        df["month"] = df["timestamp"].dt.month
        df["day_of_week"] = df["timestamp"].dt.dayofweek
        df["day_of_year"] = df["timestamp"].dt.dayofyear
        df["is_weekend"] = df["day_of_week"].isin([5, 6]).astype(int)

        # Sinusoidal encodings for periodic continuity
        df["hour_sin"] = np.sin(2 * np.pi * df["hour"] / 24.0)
        df["hour_cos"] = np.cos(2 * np.pi * df["hour"] / 24.0)
        df["month_sin"] = np.sin(2 * np.pi * df["month"] / 12.0)
        df["month_cos"] = np.cos(2 * np.pi * df["month"] / 12.0)

        # 2. Atmospheric Indices
        df["heat_index"] = df.apply(lambda r: self.calculate_heat_index(r["temperature"], r["humidity"]), axis=1)
        # Saturated vapor pressure (Tetens formula) & Relative Vapor Pressure Deficit (VPD)
        es = 0.61078 * np.exp((17.27 * df["temperature"]) / (df["temperature"] + 237.3))
        ea = es * (df["humidity"] / 100.0)
        df["vpd_kpa"] = np.maximum(0, es - ea)

        # 3. Lagged and Rolling Features per city
        cities = df["city"].unique()
        engineered_list = []

        for city in cities:
            cdf = df[df["city"] == city].copy().sort_values("timestamp")

            # Lags (assuming ~3h step: lag 1 = 3h ago, lag 2 = 6h ago, lag 8 = 24h ago)
            cdf["temp_lag_1"] = cdf["temperature"].shift(1)
            cdf["temp_lag_2"] = cdf["temperature"].shift(2)
            cdf["temp_lag_8"] = cdf["temperature"].shift(8)

            cdf["humidity_lag_1"] = cdf["humidity"].shift(1)
            cdf["pressure_lag_1"] = cdf["pressure"].shift(1)

            # Rolling statistics (6h - 24h window)
            cdf["temp_rolling_mean_6h"] = cdf["temperature"].rolling(2, min_periods=1).mean()
            cdf["temp_rolling_mean_24h"] = cdf["temperature"].rolling(8, min_periods=1).mean()
            cdf["temp_rolling_std_24h"] = cdf["temperature"].rolling(8, min_periods=1).std().fillna(0)

            # Target variables: Future temperatures (next step ~3h, next 24h ~8 steps)
            cdf["target_temp_next"] = cdf["temperature"].shift(-1)
            cdf["target_temp_24h"] = cdf["temperature"].shift(-8)

            engineered_list.append(cdf)

        full_df = pd.concat(engineered_list, ignore_index=True)

        # Drop initial NaN rows created by lagging
        feature_cols = [
            "latitude", "longitude",
            "hour_sin", "hour_cos", "month_sin", "month_cos",
            "humidity", "pressure", "wind_speed", "cloudiness",
            "heat_index", "vpd_kpa",
            "temp_lag_1", "temp_lag_2", "temp_lag_8",
            "humidity_lag_1", "pressure_lag_1",
            "temp_rolling_mean_6h", "temp_rolling_mean_24h", "temp_rolling_std_24h"
        ]

        full_df = full_df.dropna(subset=feature_cols + ["target_temp_next"]).reset_index(drop=True)
        return full_df, feature_cols

    def generate_eda_summary(self, df: pd.DataFrame) -> Dict:
        """Computes statistical summary across all monitored cities."""
        summary = {
            "total_records": len(df),
            "cities_count": df["city"].nunique(),
            "date_range": (str(df["timestamp"].min()), str(df["timestamp"].max())),
            "global_avg_temp": round(float(df["temperature"].mean()), 2),
            "global_max_temp": round(float(df["temperature"].max()), 2),
            "global_min_temp": round(float(df["temperature"].min()), 2),
            "global_avg_humidity": round(float(df["humidity"].mean()), 2),
            "global_avg_wind_speed": round(float(df["wind_speed"].mean()), 2),
            "city_stats": df.groupby("city").agg({
                "temperature": ["mean", "min", "max", "std"],
                "humidity": "mean",
                "pressure": "mean",
                "wind_speed": "mean"
            }).round(2).to_dict()
        }
        return summary

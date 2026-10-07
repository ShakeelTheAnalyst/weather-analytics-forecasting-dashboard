"""
Machine Learning Forecasting Model
Trains a Random Forest Regressor to forecast temperature variations across dynamic time horizons.
Computes evaluation metrics (RMSE, MAE, R2, MAPE) and feature importances.
"""

import logging
from pathlib import Path
from typing import Dict, Tuple, List
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.preprocessing import StandardScaler

from config import MODELS_DIR, MODEL_HYPERPARAMETERS

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class WeatherForecastModel:
    """Random Forest regressor for meteorological forecasting."""

    def __init__(self, model_params: Dict = None):
        self.params = model_params or MODEL_HYPERPARAMETERS
        self.model = RandomForestRegressor(**self.params)
        self.scaler = StandardScaler()
        self.feature_names: List[str] = []
        self.metrics: Dict[str, float] = {}

    def train(self, df: pd.DataFrame, feature_cols: List[str], target_col: str = "target_temp_next") -> Dict:
        """
        Trains model using chronological time-series split (80% train, 20% test).
        Ensures zero temporal data leakage.
        """
        self.feature_names = feature_cols
        logger.info(f"Training Random Forest on {len(df):,} samples with {len(feature_cols)} features...")

        # Chronological split
        split_idx = int(len(df) * 0.8)
        train_df = df.iloc[:split_idx]
        test_df = df.iloc[split_idx:]

        X_train = train_df[feature_cols]
        y_train = train_df[target_col]
        X_test = test_df[feature_cols]
        y_test = test_df[target_col]

        # Fit model
        self.model.fit(X_train, y_train)

        # Predictions
        y_pred_train = self.model.predict(X_train)
        y_pred_test = self.model.predict(X_test)

        # Metrics
        rmse_test = float(np.sqrt(mean_squared_error(y_test, y_pred_test)))
        mae_test = float(mean_absolute_error(y_test, y_pred_test))
        r2_test = float(r2_score(y_test, y_pred_test))
        mape_test = float(np.mean(np.abs((y_test - y_pred_test) / np.maximum(np.abs(y_test), 1e-3))) * 100)

        self.metrics = {
            "test_rmse": round(rmse_test, 3),
            "test_mae": round(mae_test, 3),
            "test_r2": round(r2_test, 4),
            "test_mape_pct": round(mape_test, 2),
            "train_r2": round(float(r2_score(y_train, y_pred_train)), 4),
            "train_samples": len(train_df),
            "test_samples": len(test_df),
        }

        logger.info(f"Model Trained Successfully! R2: {r2_test:.4f} | RMSE: {rmse_test:.3f}°C | MAE: {mae_test:.3f}°C")
        return self.metrics

    def get_feature_importances(self) -> pd.DataFrame:
        """Returns feature importances sorted descending."""
        if not hasattr(self.model, "feature_importances_"):
            raise ValueError("Model has not been trained yet.")

        importances = self.model.feature_importances_
        fi_df = pd.DataFrame({
            "Feature": self.feature_names,
            "Importance": importances
        }).sort_values(by="Importance", ascending=False).reset_index(drop=True)
        return fi_df

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Forecasts temperatures for input features."""
        return self.model.predict(X[self.feature_names])

    def forecast_trajectory(self, current_state: Dict, hours_ahead: int = 72, step_hours: int = 3) -> pd.DataFrame:
        """
        Generates forward dynamic weather forecast curve from a given current state.
        Iteratively simulates atmospheric state changes across the forecast horizon.
        """
        steps = hours_ahead // step_hours
        curr_time = pd.to_datetime(current_state.get("timestamp", pd.Timestamp.now()))
        curr_temp = float(current_state["temperature"])
        curr_humidity = float(current_state.get("humidity", 60.0))
        curr_pressure = float(current_state.get("pressure", 1013.2))
        curr_wind = float(current_state.get("wind_speed", 5.0))
        lat = float(current_state.get("latitude", 40.71))
        lon = float(current_state.get("longitude", -74.00))

        forecast_records = []
        sim_temp = curr_temp
        sim_hum = curr_humidity
        sim_press = curr_pressure

        # Rolling buffer for lag features
        temp_history = [curr_temp] * 10

        for s in range(1, steps + 1):
            future_time = curr_time + pd.Timedelta(hours=s * step_hours)
            hour = future_time.hour
            month = future_time.month

            hour_sin = np.sin(2 * np.pi * hour / 24.0)
            hour_cos = np.cos(2 * np.pi * hour / 24.0)
            month_sin = np.sin(2 * np.pi * month / 12.0)
            month_cos = np.cos(2 * np.pi * month / 12.0)

            heat_index = sim_temp + (0.05 * sim_hum)
            es = 0.61078 * np.exp((17.27 * sim_temp) / (sim_temp + 237.3))
            ea = es * (sim_hum / 100.0)
            vpd = max(0, es - ea)

            feature_dict = {
                "latitude": lat,
                "longitude": lon,
                "hour_sin": hour_sin,
                "hour_cos": hour_cos,
                "month_sin": month_sin,
                "month_cos": month_cos,
                "humidity": sim_hum,
                "pressure": sim_press,
                "wind_speed": curr_wind,
                "cloudiness": 45.0,
                "heat_index": heat_index,
                "vpd_kpa": vpd,
                "temp_lag_1": temp_history[-1],
                "temp_lag_2": temp_history[-2],
                "temp_lag_8": temp_history[-8],
                "humidity_lag_1": sim_hum,
                "pressure_lag_1": sim_press,
                "temp_rolling_mean_6h": np.mean(temp_history[-2:]),
                "temp_rolling_mean_24h": np.mean(temp_history[-8:]),
                "temp_rolling_std_24h": np.std(temp_history[-8:]) if len(temp_history) >= 8 else 1.0,
            }

            input_row = pd.DataFrame([feature_dict])
            pred_temp = float(self.model.predict(input_row[self.feature_names])[0])

            # Adjust humidity inversely to predicted temperature
            sim_hum = float(np.clip(sim_hum - (pred_temp - sim_temp) * 1.5, 25, 95))
            sim_temp = pred_temp
            temp_history.append(sim_temp)

            # Confidence interval grows slightly with horizon
            uncertainty_margin = 0.8 + (0.04 * s * step_hours)

            forecast_records.append({
                "forecast_step": s,
                "horizon_hours": s * step_hours,
                "forecast_timestamp": future_time,
                "predicted_temp": round(pred_temp, 2),
                "lower_bound": round(pred_temp - uncertainty_margin, 2),
                "upper_bound": round(pred_temp + uncertainty_margin, 2),
                "predicted_humidity": round(sim_hum, 1),
                "model_confidence": round(max(65.0, 96.5 - (0.45 * s * step_hours)), 1),
            })

        return pd.DataFrame(forecast_records)

    def save(self, filepath: Path = None):
        """Saves model and metadata to disk."""
        target_path = filepath or (MODELS_DIR / "random_forest_weather_model.joblib")
        payload = {
            "model": self.model,
            "feature_names": self.feature_names,
            "metrics": self.metrics,
            "params": self.params,
        }
        joblib.dump(payload, target_path)
        logger.info(f"Model artifact saved to {target_path}")

    @classmethod
    def load(cls, filepath: Path = None) -> "WeatherForecastModel":
        """Loads serialized model artifact."""
        target_path = filepath or (MODELS_DIR / "random_forest_weather_model.joblib")
        if not target_path.exists():
            raise FileNotFoundError(f"Model file not found at {target_path}")
        payload = joblib.load(target_path)
        instance = cls(model_params=payload.get("params"))
        instance.model = payload["model"]
        instance.feature_names = payload["feature_names"]
        instance.metrics = payload.get("metrics", {})
        return instance

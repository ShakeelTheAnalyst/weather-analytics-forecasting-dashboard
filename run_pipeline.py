"""
Master Pipeline Runner
Executes the end-to-end meteorological pipeline:
  1. Data Ingestion (OpenWeatherMap API + Multi-City History)
  2. Statistical EDA & Anomaly Detection (Z-Score & Pressure Delta)
  3. Feature Engineering & Random Forest Model Training
  4. Dynamic Forward Forecasting (3h - 72h horizons)
  5. Star Schema Power BI Export
"""

import sys
import logging
from datetime import datetime
import pandas as pd

from src.api_pipeline import WeatherDataPipeline
from src.eda_processor import WeatherEDAProcessor
from src.ml_model import WeatherForecastModel
from src.powerbi_export import PowerBIDataExporter

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("PipelineRunner")


def run_full_pipeline(days_history: int = 60):
    logger.info("=" * 70)
    logger.info("STARTING END-TO-END METEOROLOGICAL ANALYTICS & FORECASTING PIPELINE")
    logger.info("=" * 70)

    # Step 1: Ingestion
    logger.info("\n>>> STEP 1: Ingestion Pipeline")
    pipeline = WeatherDataPipeline()
    raw_df = pipeline.generate_historical_dataset(days=days_history, sample_interval_hours=3)
    logger.info(f"Ingested {len(raw_df):,} raw meteorological records across {raw_df['city'].nunique()} cities.")

    # Step 2: EDA & Anomaly Detection
    logger.info("\n>>> STEP 2: Statistical EDA & Anomaly Detection")
    eda = WeatherEDAProcessor()
    anomaly_df = eda.detect_anomalies(raw_df)
    anom_count = anomaly_df['is_anomaly'].sum()
    logger.info(f"Anomaly Detection Completed: Flagged {anom_count:,} anomalies ({anom_count/len(anomaly_df)*100:.2f}% of total).")
    logger.info(f"Severity Breakdown:\n{anomaly_df['anomaly_severity'].value_counts().to_string()}")

    # Step 3: Feature Engineering & ML Training
    logger.info("\n>>> STEP 3: Feature Engineering & Random Forest Regressor Training")
    featured_df, feature_cols = eda.engineer_ml_features(anomaly_df)
    logger.info(f"Engineered {len(feature_cols)} predictive features across {len(featured_df):,} training rows.")

    model = WeatherForecastModel()
    metrics = model.train(featured_df, feature_cols=feature_cols, target_col="target_temp_next")
    model.save()

    logger.info("\nModel Performance Evaluation:")
    logger.info(f"  • Test R² Score:   {metrics['test_r2']:.4f} (Variance Explained)")
    logger.info(f"  • Test RMSE:       {metrics['test_rmse']:.3f} °C")
    logger.info(f"  • Test MAE:        {metrics['test_mae']:.3f} °C")
    logger.info(f"  • Test MAPE:       {metrics['test_mape_pct']:.2f} %")

    fi = model.get_feature_importances()
    logger.info("\nTop 5 Predictive Features:")
    for _, row in fi.head(5).iterrows():
        logger.info(f"  - {row['Feature']}: {row['Importance']:.4f}")

    # Step 4: Multi-Horizon Forecasting
    logger.info("\n>>> STEP 4: Generating Dynamic Forward Forecast Curves (3h to 72h)")
    all_forecasts = []
    latest_points = anomaly_df.sort_values("timestamp").groupby("city").last().reset_index()

    for _, city_row in latest_points.iterrows():
        city_state = city_row.to_dict()
        fc_df = model.forecast_trajectory(city_state, hours_ahead=72, step_hours=3)
        fc_df["city"] = city_row["city"]
        all_forecasts.extend(fc_df.to_dict(orient="records"))

    logger.info(f"Generated {len(all_forecasts):,} forecast horizon points.")

    # Step 5: Power BI Star Schema Export
    logger.info("\n>>> STEP 5: Exporting Production Star Schema for Power BI")
    exporter = PowerBIDataExporter()
    dim_city = exporter.generate_dim_city()

    min_date = anomaly_df["timestamp"].min().strftime("%Y-%m-%d")
    max_forecast_date = (anomaly_df["timestamp"].max() + pd.Timedelta(days=5)).strftime("%Y-%m-%d")
    dim_date = exporter.generate_dim_date(min_date, max_forecast_date)

    fact_obs = exporter.generate_fact_observations(anomaly_df, dim_city)
    fact_fc = exporter.generate_fact_forecasts(all_forecasts, dim_city)

    logger.info("=" * 70)
    logger.info("PIPELINE COMPLETED SUCCESSFULLY!")
    logger.info(f"  • Fact_Weather_Observations: {len(fact_obs):,} rows")
    logger.info(f"  • Fact_Weather_Forecasts:    {len(fact_fc):,} rows")
    logger.info(f"  • Dim_City:                  {len(dim_city)} rows")
    logger.info(f"  • Dim_Date:                  {len(dim_date)} rows")
    logger.info("All Power BI datasets are ready in data/processed/")
    logger.info("=" * 70)


if __name__ == "__main__":
    run_full_pipeline(days_history=60)

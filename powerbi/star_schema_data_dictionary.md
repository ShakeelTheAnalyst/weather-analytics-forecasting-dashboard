# Power BI Star Schema Data Dictionary

This document details the dimensional model used by the **Real-Time Weather Analytics & Forecasting Dashboard**. The schema is optimized for analytical query performance and DAX measure calculations in Microsoft Power BI Desktop and Power BI Service.

---

## 🏗️ Architecture Diagram

```
                 ┌─────────────────────────────────┐
                 │            Dim_City             │
                 ├─────────────────────────────────┤
                 │ PK  CityKey (Int)               │
                 │     CityName (Text)             │
                 │     Country (Text)              │
                 │     Region (Text)               │
                 │     Latitude (Float)            │
                 │     Longitude (Float)           │
                 │     Coordinates (Text)          │
                 │     ClimateZone (Text)          │
                 │     Population (Int)            │
                 └───────────────┬─────────────────┘
                                 │
                     1           │
                     ────────────┤
                                 │
                                 │ *
                 ┌───────────────▼─────────────────┐
                 │    Fact_Weather_Observations   │
                 ├─────────────────────────────────┤
                 │ PK  ObservationID (Int)         │
                 │ FK  CityKey (Int)               │
                 │ FK  DateKey (Int)               │
                 │     ObservationTimestamp (DT)   │
                 │     Temperature_C (Float)       │
                 │     Temperature_F (Float)       │
                 │     FeelsLike_C (Float)         │
                 │     Temp_Min_C / Temp_Max_C     │
                 │     Humidity_Pct (Float)        │
                 │     Pressure_hPa (Float)        │
                 │     WindSpeed_mps (Float)       │
                 │     WindDirection_deg (Int)     │
                 │     Cloudiness_Pct (Int)        │
                 │     WeatherCondition (Text)     │
                 │     WeatherDescription (Text)   │
                 │     HeatIndex_C (Float)         │
                 │     VPD_kPa (Float)             │
                 │     Is_Anomaly (Boolean)        │
                 │     Anomaly_Severity (Text)     │
                 │     Anomaly_Reason (Text)       │
                 │     Z_Score (Float)             │
                 │     Pressure_Delta_3h (Float)   │
                 └───────────────▲─────────────────┘
                                 │
                                 │ *
                     ────────────┤
                     1           │
                 ┌───────────────┴─────────────────┐
                 │            Dim_Date             │
                 ├─────────────────────────────────┤
                 │ PK  DateKey (Int - YYYYMMDD)    │
                 │     Date (Date)                 │
                 │     Year (Int)                  │
                 │     Quarter (Text - Q1..Q4)     │
                 │     MonthNum (Int)              │
                 │     MonthName (Text)            │
                 │     MonthShort (Text)           │
                 │     DayOfMonth (Int)            │
                 │     DayOfWeek (Int)             │
                 │     DayOfWeekName (Text)        │
                 │     IsWeekend (Text - Yes/No)   │
                 │     Season (Text)               │
                 └───────────────┬─────────────────┘
                                 │
                     1           │
                     ────────────┤
                                 │
                                 │ *
                 ┌───────────────▼─────────────────┐
                 │     Fact_Weather_Forecasts      │
                 ├─────────────────────────────────┤
                 │ PK  ForecastID (Int)            │
                 │ FK  CityKey (Int)               │
                 │ FK  DateKey (Int)               │
                 │     ForecastTimestamp (DT)      │
                 │     Horizon_Hours (Int - 3..72) │
                 │     Predicted_Temp_C (Float)    │
                 │     Lower_Bound_C (Float)       │
                 │     Upper_Bound_C (Float)       │
                 │     Predicted_Humidity_Pct      │
                 │     Model_Confidence_Pct        │
                 │     Forecast_Accuracy_Pct       │
                 └─────────────────────────────────┘
```

---

## 📋 Dimension Tables

### 1. `Dim_City` (`dim_city.csv`)
| Column | Data Type | Description | Sample Value |
|---|---|---|---|
| `CityKey` | Integer (PK) | Surrogate primary key | `1` |
| `CityName` | Text | Name of monitored city | `New York` |
| `Country` | Text | Country name | `USA` |
| `Region` | Text | Geographic region | `North America` |
| `Latitude` | Decimal | Geocoded latitude coordinate | `40.7128` |
| `Longitude` | Decimal | Geocoded longitude coordinate | `-74.0060` |
| `Coordinates` | Text | Lat/Lon string for Power BI Map visual | `40.7128,-74.0060` |
| `ClimateZone` | Text | Köppen meteorological classification | `Humid Continental` |
| `Population` | Integer | Estimated metropolitan population | `8,336,000` |

### 2. `Dim_Date` (`dim_date.csv`)
| Column | Data Type | Description | Sample Value |
|---|---|---|---|
| `DateKey` | Integer (PK) | Surrogate key in format `YYYYMMDD` | `20261007` |
| `Date` | Date | Calendar date | `2026-10-07` |
| `Year` | Integer | Calendar year | `2026` |
| `Quarter` | Text | Quarter notation | `Q4` |
| `MonthNum` | Integer | Month number (1–12) | `10` |
| `MonthName` | Text | Full month name | `October` |
| `DayOfWeek` | Integer | Day of week index (1 = Monday) | `3` |
| `DayOfWeekName`| Text | Day of week name | `Wednesday` |
| `IsWeekend` | Text | Flag `Yes` or `No` | `No` |
| `Season` | Text | Climatological season | `Autumn` |

---

## 📊 Fact Tables

### 3. `Fact_Weather_Observations` (`fact_weather_observations.csv`)
Contains historical and real-time weather streams ingested via OpenWeatherMap API with statistical anomaly diagnostics.

| Column | Data Type | Description |
|---|---|---|
| `ObservationID` | Integer (PK) | Unique observation record identifier |
| `CityKey` | Integer (FK) | Reference to `Dim_City[CityKey]` |
| `DateKey` | Integer (FK) | Reference to `Dim_Date[DateKey]` |
| `ObservationTimestamp` | DateTime | Timestamp of the meteorological reading |
| `Temperature_C` | Decimal | Ambient temperature in Celsius |
| `Temperature_F` | Decimal | Ambient temperature in Fahrenheit |
| `FeelsLike_C` | Decimal | Apparent temperature in Celsius |
| `Humidity_Pct` | Decimal | Relative humidity percentage (0-100%) |
| `Pressure_hPa` | Decimal | Atmospheric barometric pressure in hectopascals |
| `WindSpeed_mps` | Decimal | Wind velocity in meters per second |
| `WindDirection_deg` | Integer | Wind vector in degrees (0–360°) |
| `Cloudiness_Pct` | Integer | Cloud cover percentage (0-100%) |
| `WeatherCondition` | Text | Weather category (`Clear`, `Clouds`, `Rain`, etc.) |
| `HeatIndex_C` | Decimal | Steadman Heat Index calculation |
| `VPD_kPa` | Decimal | Vapor Pressure Deficit in kilopascals |
| `Is_Anomaly` | Boolean | TRUE if flagged by Z-score, IQR, or pressure drop |
| `Anomaly_Severity`| Text | Severity level: `Normal`, `Moderate Warning`, `Severe Anomaly` |
| `Anomaly_Reason` | Text | Root-cause diagnostic explanation |
| `Z_Score` | Decimal | Climatological deviation score (in standard deviations) |
| `Pressure_Delta_3h`| Decimal | 3-hour barometric delta (rapid pressure drops indicate storms) |

### 4. `Fact_Weather_Forecasts` (`fact_weather_forecasts.csv`)
Contains predictive temperature curves generated by the Scikit-Learn Random Forest regressor across dynamic horizons (3h to 72h).

| Column | Data Type | Description |
|---|---|---|
| `ForecastID` | Integer (PK) | Unique forecast identifier |
| `CityKey` | Integer (FK) | Reference to `Dim_City[CityKey]` |
| `DateKey` | Integer (FK) | Reference to `Dim_Date[DateKey]` |
| `ForecastTimestamp`| DateTime | Projected future timestamp |
| `Horizon_Hours` | Integer | Lead time in hours (+3, +6, +12, +24, +48, +72) |
| `Predicted_Temp_C` | Decimal | Random Forest regression inference (°C) |
| `Lower_Bound_C` | Decimal | 95% Confidence Interval lower bound |
| `Upper_Bound_C` | Decimal | 95% Confidence Interval upper bound |
| `Predicted_Humidity_Pct`| Decimal | Atmospheric simulation projected humidity |
| `Model_Confidence_Pct` | Decimal | Algorithmic prediction confidence score (65-98%) |
| `Forecast_Accuracy_Pct`| Decimal | Model accuracy metric |

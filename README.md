# ⚡ Real-Time Weather Analytics & Forecasting Dashboard

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.30+-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io)
[![Power BI](https://img.shields.io/badge/Power_BI-Desktop_%26_Service-F2C811?style=for-the-badge&logo=powerbi&logoColor=black)](https://powerbi.microsoft.com)
[![Scikit-Learn](https://img.shields.io/badge/scikit--learn-Random_Forest-F7931E?style=for-the-badge&logo=scikit-learn&logoColor=white)](https://scikit-learn.org)
[![Pandas](https://img.shields.io/badge/Pandas-Data_Engineering-150458?style=for-the-badge&logo=pandas&logoColor=white)](https://pandas.pydata.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-purple.svg?style=for-the-badge)](LICENSE)

> **End-to-End Meteorological Data Pipeline, Machine Learning Forecasting Engine, and Interactive Power BI Executive Dashboard.**

An interactive meteorological data analytics and machine learning application. It consumes real-time weather streams via the **OpenWeatherMap API**, executes automated exploratory data analysis (**EDA**), flags climatological anomalies using calibrated **Z-score** and barometric plummet algorithms, and leverages a trained **Random Forest regressor** to forecast temperature variations across dynamic time windows (+3h to +72h).

**Impact:** Replaced static climate reports with automated real-time data ingestion, statistical anomaly detection, and predictive temperature curves presented in an interactive **Streamlit UI** and an enterprise **Power BI Star Schema Dashboard**.

---

## 🌟 Key Highlights & Capabilities

- **🛰️ Live API Ingestion Pipeline**: Ingests real-time meteorological observations for 12 global metropolises via OpenWeatherMap API with mathematical synthetic generation fallback.
- **🔬 Statistical EDA & Anomaly Detection**: Dual-layer anomaly detection flagging extreme heat spikes, cold plunges ($\ge 2.8\sigma$ climatological Z-score), and abrupt barometric pressure plunges (storm warning fronts).
- **🤖 Random Forest ML Forecasting**: Multi-step recursive regressor predicting temperatures across 3h, 6h, 12h, 24h, 48h, and 72h horizons with 95% confidence bands ($R^2 = 0.858$, $\text{RMSE} = 2.20^\circ\text{C}$, $\text{MAE} = 1.45^\circ\text{C}$).
- **📐 Power BI Star Schema Data Model**: Pre-cleaned dimensional tables (`Dim_City`, `Dim_Date`, `Fact_Weather_Observations`, `Fact_Weather_Forecasts`) engineered specifically for high-performance Power BI reporting.
- **🎨 Modern Dark Aurora Visual Theme**: Custom visual theme (`powerbi_theme.json`) matching modern violet/slate portfolio aesthetics.
- **💻 Interactive Streamlit Web UI**: Real-time KPI cards, interactive Plotly time series, correlation heatmaps, feature importance charts, and a "What-If" climate scenario simulator.
- **🌐 Interactive Power BI Web Preview**: Standalone HTML dashboard preview (`powerbi/dashboard_preview.html`) allowing anyone to experience the Power BI executive view without installing desktop software.

---

## 🏗️ Architecture & Data Flow

```mermaid
flowchart TD
    subgraph Data_Ingestion ["1. Ingestion Layer"]
        API[OpenWeatherMap REST API] --> Ingest[api_pipeline.py]
        SimEngine[Synthetic Climatology Fallback Engine] --> Ingest
        Ingest --> RawCSV[(data/raw/)]
    end

    subgraph Data_Processing ["2. EDA & Feature Engineering"]
        Ingest --> EDA[eda_processor.py]
        EDA --> AnomDetect[Statistical Anomaly Detection\nZ-Score >= 2.8σ & Pressure Delta]
        AnomDetect --> FeatureEng[Temporal Cyclical Encoding\nLag Features & Atmospheric Indices]
    end

    subgraph ML_Forecasting ["3. Machine Learning Model"]
        FeatureEng --> RF[ml_model.py\nRandom Forest Regressor]
        RF --> Metrics[Evaluation:\nR² = 0.858 | RMSE = 2.20°C | MAE = 1.45°C]
        RF --> SaveModel[(models/random_forest_weather_model.joblib)]
        RF --> ForwardSim[Multi-Horizon Forecasts\n+3h to +72h with 95% Confidence]
    end

    subgraph Dimensional_Modeling ["4. Star Schema Power BI Export"]
        ForwardSim --> PBIExport[powerbi_export.py]
        EDA --> PBIExport
        PBIExport --> DimCity[(Dim_City.csv)]
        PBIExport --> DimDate[(Dim_Date.csv)]
        PBIExport --> FactObs[(Fact_Weather_Observations.csv)]
        PBIExport --> FactFC[(Fact_Weather_Forecasts.csv)]
    end

    subgraph Presentation_Layer ["5. Presentation & Delivery"]
        PBIExport --> PBIReport[Power BI Executive Dashboard\n26 DAX Measures & Dark Theme]
        PBIExport --> StreamlitApp[Streamlit Interactive UI\napp.py]
        PBIReport --> Portfolio[Personal Portfolio Showcase\nView Project ↗ & GitHub Repo]
    end
```

---

## 📊 Power BI Dimensional Star Schema

The exported dataset strictly adheres to analytical dimensional modeling standards:

```
                  ┌─────────────────────────┐
                  │        Dim_City         │
                  ├─────────────────────────┤
                  │ PK  CityKey             │
                  │     CityName, Country   │
                  │     Latitude, Longitude │
                  │     ClimateZone         │
                  └────────────┬────────────┘
                               │
                   1           │
                   ────────────┤
                               │
                               │ *
               ┌───────────────▼────────────────┐
               │   Fact_Weather_Observations   │
               ├────────────────────────────────┤
               │ PK  ObservationID              │
               │ FK  CityKey                    │
               │ FK  DateKey                    │
               │     ObservationTimestamp       │
               │     Temperature_C, Temp_F      │
               │     Humidity_Pct, Pressure_hPa │
               │     HeatIndex_C, VPD_kPa       │
               │     Is_Anomaly, Anomaly_Reason │
               │     Z_Score, Pressure_Delta_3h │
               └───────────────▲────────────────┘
                               │
                               │ *
                   ────────────┤
                   1           │
                  ┌────────────┴────────────┐
                  │        Dim_Date         │
                  ├─────────────────────────┤
                  │ PK  DateKey (YYYYMMDD)  │
                  │     Date, Year, Month   │
                  │     Quarter, IsWeekend  │
                  └─────────────────────────┘
```

---

## 💡 Highlight DAX Measures

The project includes **26 production-grade DAX measures** in [`powerbi/dax_measures.dax`](powerbi/dax_measures.dax):

```dax
// 1. Average Temperature (°C)
Avg Temperature C = AVERAGE(Fact_Weather_Observations[Temperature_C])

// 2. Anomaly Incident Rate (%)
Anomaly Rate Pct = 
DIVIDE(
    CALCULATE(COUNTROWS(Fact_Weather_Observations), Fact_Weather_Observations[Is_Anomaly] = TRUE()),
    COUNTROWS(Fact_Weather_Observations),
    0
) * 100

// 3. 7-Day Rolling Climatological Moving Average
7D Rolling Avg Temp C = 
CALCULATE(
    [Avg Temperature C],
    DATESINPERIOD(
        Dim_Date[Date],
        LASTDATE(Dim_Date[Date]),
        -7,
        DAY
    )
)

// 4. ML Forecast Accuracy (%)
Forecast Accuracy Pct = AVERAGE(Fact_Weather_Forecasts[Forecast_Accuracy_Pct])
```

---

## 📁 Repository Directory Structure

```
Weather Analytics Project/
├── .env.example                     # Environment template for OpenWeatherMap API key
├── .gitignore                       # Production gitignore for Python, secrets, and Power BI cache
├── README.md                        # Master repository documentation
├── requirements.txt                 # Pinned project dependencies
├── config.py                        # Centralized configuration (cities, hyperparameters, paths)
├── run_pipeline.py                  # One-command end-to-end execution script
├── app.py                           # Interactive Streamlit application
├── data/
│   ├── raw/                         # Raw API timestamped JSON/CSV snapshots
│   └── processed/                   # Power BI Star Schema datasets
│       ├── dim_city.csv             # Dimension: Monitored Metropolises
│       ├── dim_date.csv             # Dimension: Temporal Calendar Keys
│       ├── fact_weather_observations.csv # Fact: Historical & Real-Time Weather Observations
│       ├── fact_weather_forecasts.csv    # Fact: ML Forecast Horizons (+3h to +72h)
│       └── historical_weather_dataset.csv
├── models/
│   └── random_forest_weather_model.joblib # Serialized Scikit-Learn Model
├── powerbi/
│   ├── dax_measures.dax             # 26 Production DAX measures with commentary
│   ├── powerbi_theme.json           # Dark Aurora theme for Power BI Desktop
│   ├── star_schema_data_dictionary.md # Complete column specifications and data types
│   ├── powerbi_dashboard_guide.md   # Step-by-step 5-minute visual build manual
│   └── dashboard_preview.html       # Standalone interactive browser preview of Power BI report
└── src/
    ├── __init__.py
    ├── api_pipeline.py              # Live API ingestion + realistic synthetic fallback
    ├── eda_processor.py             # Statistical EDA & Z-score anomaly detection engine
    ├── ml_model.py                  # Random Forest Regressor & lag feature engineering
    └── powerbi_export.py            # Star Schema export engine
```

---

## 🚀 Quickstart Guide

### 1. Clone & Set Up Environment

```bash
git clone https://github.com/ShakeelTheAnalyst/weather-analytics-forecasting-dashboard.git
cd weather-analytics-forecasting-dashboard

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
.\venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure API Key (Optional)

Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Add your free [OpenWeatherMap API Key](https://openweathermap.org/api). If left empty, the pipeline will seamlessly utilize the mathematical climate simulator with zero errors.

### 3. Run the End-to-End Pipeline

Execute the master pipeline to ingest data, run statistical EDA, train the Random Forest regressor, and generate the Power BI Star Schema tables:

```bash
python run_pipeline.py
```

*Output summary:*
```
>>> STEP 1: Ingested 5,760 raw meteorological records across 12 cities.
>>> STEP 2: Flagged 813 anomalies (Z-score >= 2.8σ and pressure drops).
>>> STEP 3: Model Trained! R² = 0.8576 | RMSE = 2.203°C | MAE = 1.453°C
>>> STEP 4: Generated 288 forward forecast horizon points (+3h to +72h).
>>> STEP 5: Exported Dim_City, Dim_Date, Fact_Observations, and Fact_Forecasts to data/processed/
```

### 4. Launch the Interactive Streamlit Web UI

```bash
# Recommended on Windows:
python -m streamlit run app.py

# Or double-click the included run_app.bat launcher in your project folder!
```
Open your browser at `http://localhost:8501`.

---

## 📊 Building the Power BI Dashboard

1. Open **Power BI Desktop**.
2. Click **Get Data** > **Text/CSV** and select the 4 CSV files in `data/processed/`:
   - `dim_city.csv`
   - `dim_date.csv`
   - `fact_weather_observations.csv`
   - `fact_weather_forecasts.csv`
3. Click **Load**.
4. In **Model View**, verify the 1-to-Many relationships connect on `CityKey` and `DateKey`.
5. Go to **View** > **Themes** > **Browse for Themes** and select `powerbi/powerbi_theme.json`.
6. Copy the DAX measures from `powerbi/dax_measures.dax`.
7. Refer to [`powerbi/powerbi_dashboard_guide.md`](powerbi/powerbi_dashboard_guide.md) for visual layout instructions.

> **Tip:** You can double-click `powerbi/dashboard_preview.html` to instantly inspect how the finished Power BI dashboard looks directly in any browser!

---

## 🔗 Adding to Your Portfolio

To connect this project to your portfolio card:

1. **GitHub Repository Button**:
   - Push this codebase to your GitHub:
     ```bash
     git init
     git add .
     git commit -m "feat: complete end-to-end weather analytics and Power BI dashboard"
     git branch -M main
     git remote add origin https://github.com/ShakeelTheAnalyst/weather-analytics-forecasting-dashboard.git
     git push -u origin main
     ```
   - Repository URL: `https://github.com/ShakeelTheAnalyst/weather-analytics-forecasting-dashboard`

2. **View Project Button**:
   - Option A: Publish your Power BI report to Power BI Service, click **File** > **Embed report** > **Publish to web (public)**, and paste the URL into your portfolio's **`View Project ↗`** button.
   - Option B: Host `powerbi/dashboard_preview.html` via GitHub Pages (or deploy `app.py` via Streamlit Community Cloud for free) and link that URL!

---

## 📈 Model Performance & Evaluation

| Metric | Random Forest Score | Benchmark / Threshold | Status |
|---|---|---|---|
| **$R^2$ Score** | **0.8576** | $> 0.80$ | 🟢 Optimal |
| **RMSE** | **2.203 °C** | $< 2.50\text{ }^\circ\text{C}$ | 🟢 High Precision |
| **MAE** | **1.453 °C** | $< 1.80\text{ }^\circ\text{C}$ | 🟢 High Accuracy |
| **Forecast Horizons** | **+3h to +72h** | Multi-Step Recursive | 🟢 Complete |

---

## 📜 License

Distributed under the MIT License. See `LICENSE` for more information.

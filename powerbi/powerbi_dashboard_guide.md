# Complete Power BI Desktop Setup Guide

Follow this guide to build the **Real-Time Weather Analytics & Forecasting Power BI Dashboard** using the pre-generated Star Schema CSV files.

---

## ⚡ Quick 5-Minute Setup

### Step 1: Open Power BI Desktop & Load Data
1. Open **Power BI Desktop**.
2. Click **Get Data** > **Text/CSV**.
3. Navigate to `data/processed/` in this repository and load the following 4 files:
   - `dim_city.csv`
   - `dim_date.csv`
   - `fact_weather_observations.csv`
   - `fact_weather_forecasts.csv`
4. Click **Load** (no Power Query transformations needed — data is pre-cleaned in the Python pipeline).

---

### Step 2: Establish Model Relationships (Star Schema)
Navigate to the **Model View** (left sidebar icon with boxes) and verify the 1-to-Many (`1:*`) relationships:

1. **`Dim_City[CityKey]`** ───(1 to Many)───► **`Fact_Weather_Observations[CityKey]`**
   - Cardinality: `One to Many (1:*)`
   - Cross filter direction: `Single`

2. **`Dim_Date[DateKey]`** ───(1 to Many)───► **`Fact_Weather_Observations[DateKey]`**
   - Cardinality: `One to Many (1:*)`
   - Cross filter direction: `Single`

3. **`Dim_City[CityKey]`** ───(1 to Many)───► **`Fact_Weather_Forecasts[CityKey]`**
   - Cardinality: `One to Many (1:*)`
   - Cross filter direction: `Single`

4. **`Dim_Date[DateKey]`** ───(1 to Many)───► **`Fact_Weather_Forecasts[DateKey]`**
   - Cardinality: `One to Many (1:*)`
   - Cross filter direction: `Single`

---

### Step 3: Apply the Custom Dark Aurora Theme
1. In the top ribbon, navigate to **View** > **Themes** dropdown.
2. Select **Browse for Themes...**.
3. Choose `powerbi/powerbi_theme.json` from this repository.
4. The canvas, background, fonts, and visual cards will instantly adopt the portfolio's modern dark purple aesthetic!

---

### Step 4: Import DAX Measures
Create a dedicated table called `_Measures` or add the measures to `Fact_Weather_Observations`:
1. In the **Home** tab, click **Enter Data** and name the table `_Measures`.
2. Open `powerbi/dax_measures.dax` in any text editor.
3. Copy and paste each measure into Power BI (e.g., `[Avg Temperature C]`, `[Anomaly Count]`, `[Predicted Temperature C]`).

---

## 🖥️ Dashboard Page Blueprint

### 📄 Page 1: Global Weather Command Center
*Executive overview of current meteorological conditions across global metropolises.*

- **Top KPI Cards (5 Cards in a row):**
  - Card 1: `[Avg Temperature C]` (Target: Current global mean)
  - Card 2: `[Avg Humidity Pct]`
  - Card 3: `[Avg Barometric Pressure]`
  - Card 4: `[Anomaly Count]` (Callout value in Red `#EF4444`)
  - Card 5: `[Overall Forecast Accuracy Pct]`
- **Global Map Visual (Left half):**
  - Visual: **Azure Map** or **Filled Map / Bubble Map**
  - Location: `Dim_City[Latitude]`, `Dim_City[Longitude]`
  - Bubble Size: `[Avg Humidity Pct]`
  - Bubble Color: `[Avg Temperature C]`
- **City Weather Matrix (Right half):**
  - Table visual: `Dim_City[CityName]`, `[Avg Temperature C]`, `[Avg Feels Like C]`, `[Avg Wind Speed]`, `Fact_Weather_Observations[WeatherCondition]`, `[Anomaly Count]`
  - Conditional Formatting: Background data bars on Temperature.
- **Top Slicers:**
  - Slicer 1: `Dim_City[Region]`
  - Slicer 2: `Dim_Date[MonthName]`

---

### 📄 Page 2: Machine Learning Forecasting & Anomaly Hub
*Predictive modeling curves and automated meteorological anomaly detection.*

- **Forecast vs Horizon Line Chart:**
  - Visual: **Line Chart**
  - X-Axis: `Fact_Weather_Forecasts[ForecastTimestamp]`
  - Values: `[Predicted Temperature C]`, `[Forecast Upper Bound C]`, `[Forecast Lower Bound C]`
  - Legend: Metric Name
- **Feature Importance Bar Chart:**
  - Visual: **Clustered Bar Chart** (Horizontal)
  - Category: Features (`temp_lag_8`, `heat_index`, `hour_cos`, `temp_rolling_mean_24h`, etc.)
  - Value: Feature Importance score
- **Anomaly Severity Donut Chart:**
  - Visual: **Donut Chart**
  - Legend: `Fact_Weather_Observations[Anomaly_Severity]`
  - Values: `[Anomaly Count]`
- **Incident Alert Table:**
  - Visual: **Table**
  - Columns: `ObservationTimestamp`, `CityName`, `Temperature_C`, `Z_Score`, `Pressure_Delta_3h`, `Anomaly_Reason`

---

### 📄 Page 3: City Microclimate Deep Dive
*Drill-through analysis for specific cities, diurnal trends, and microclimates.*

- **City Filter Slicer:** Dropdown with `Dim_City[CityName]`.
- **Diurnal Solar Cycle Line Chart:**
  - X-Axis: `Dim_Date[HourOfDay]` (0 to 23)
  - Lines: Average Temperature and Average Humidity on dual Y-axis.
- **7-Day Rolling Moving Average:**
  - Line chart showing raw temperature vs `[7D Rolling Avg Temp C]`.
- **Weather Condition Distribution:**
  - Treemap visual showing breakdown of conditions (`Clear`, `Clouds`, `Rain`).

---

## 🌐 Linking Power BI to Your Portfolio & GitHub

1. **Publish to Power BI Service**:
   - In Power BI Desktop, click **Publish** (Home ribbon) to your workspace.
2. **Generate Interactive Web Link (Public Portfolio View)**:
   - In Power BI Service, go to **File** > **Embed report** > **Publish to web (public)**.
   - Copy the generated URL (e.g. `https://app.powerbi.com/view?r=...`).
3. **Paste in Portfolio**:
   - In your portfolio card's `View Project` button, paste your Power BI embed URL!
4. **Link GitHub**:
   - In the `GitHub Repo` button, link your GitHub repository URL.

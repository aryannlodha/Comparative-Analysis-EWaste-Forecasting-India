# Power BI Dashboard Implementation Guide & Architecture Specification

**Project Title:** Comparative Analysis of Predictive Models for E-Waste Generation Forecasting in India  
**Course/Domain:** Enterprise Information Systems (EIS)  
**Target Platform:** Microsoft Power BI Desktop / Power BI Service  

---

## 1. Overview and Architecture

This guide details the complete configuration required to reproduce the decision-support dashboard in Microsoft Power BI. All input files are stored in `outputs/power_bi/` as clean, validated CSV files.

### 1.1 Data Files Manifest
1. `historical_data.csv`: Verified annual national e-waste generation figures (FY 2017–18 to FY 2024–25), reporting frameworks, and metadata.
2. `forecast_results.csv`: Future multi-model forecasts (FY 2025–26 to FY 2030–31) across 6 models, alongside historical benchmarks and uncertainty bounds.
3. `model_metrics.csv`: Comparative evaluation metrics (MAE, RMSE, MAPE, sMAPE) from rolling-origin backtesting.
4. `model_predictions.csv`: Detailed fold-by-fold predictions and residuals during chronological evaluation.
5. `model_robustness_results.csv`: Sensitivity test results (training data contraction, missing observation drop-one tests, Gaussian noise perturbation, and Gaussian Process uncertainty).
6. `data_quality_report.csv`: Complete data audit log documenting exclusions, methodology discrepancies, and verification actions.
7. `source_register.csv`: Complete source provenance including regulatory frameworks, official release URLs, and coverage notes.

---

## 2. Power BI Data Model (Star Schema)

```
                    ┌─────────────────────────┐
                    │      SourceRegister     │
                    │   (source_register.csv) │
                    └────────────┬────────────┘
                                 │ 1
                                 │
                                 │ *
┌─────────────────────────┐      │      ┌─────────────────────────┐
│     HistoricalData      ├──────┼─────►│     ForecastResults     │
│  (historical_data.csv)  │      │      │  (forecast_results.csv) │
└────────────┬────────────┘      │      └────────────┬────────────┘
             │ 1                 │                   │ *
             │                   │                   │
             │ *                 │                   │ 1
┌────────────▼────────────┐      │      ┌────────────▼────────────┐
│    DataQualityReport    │      └─────►│       ModelMetrics      │
│(data_quality_report.csv)│             │   (model_metrics.csv)   │
└─────────────────────────┘             └────────────┬────────────┘
                                                     │ 1
                                                     │
                                                     │ *
                                        ┌────────────▼────────────┐
                                        │    ModelPredictions     │
                                        │ (model_predictions.csv) │
                                        └─────────────────────────┘
```

### Table Relationships:
- **`ForecastResults` [financial_year]** <──> **`HistoricalData` [financial_year]** (1-to-Many or Many-to-1, Cross-filter: Both)
- **`HistoricalData` [source_id]** <──> **`SourceRegister` [Source_ID]** (Many-to-1)
- **`ModelMetrics` [Model]** <──> **`ForecastResults` [model]** (1-to-Many)
- **`ModelMetrics` [Model]** <──> **`ModelPredictions` [model]** (1-to-Many)

---

## 3. DAX Core Measures

Create a dedicated measure table called `_Measures`:

```dax
// 1. Latest Verified Historical Generation (Metric Tonnes)
Latest_Historical_Generation_MT = 
CALCULATE(
    MAX(HistoricalData[ewaste_generated_tonnes]),
    HistoricalData[financial_year] = "2024-25"
)

// 2. Latest Historical Generation (Kilotonnes)
Latest_Historical_Generation_KT = 
[Latest_Historical_Generation_MT] / 1000

// 3. 2030 Baseline Forecast (Linear Regression with Framework Adjustment)
Forecast_2030_LinRegFW_MT = 
CALCULATE(
    SUM(ForecastResults[forecast_tonnes]),
    ForecastResults[financial_year] = "2030-31",
    ForecastResults[model] = "Linear Regression (FW)"
)

// 4. Forecast Growth vs 2024-25 Baseline (%)
Forecast_Growth_2030_Pct = 
DIVIDE(
    [Forecast_2030_LinRegFW_MT] - [Latest_Historical_Generation_MT],
    [Latest_Historical_Generation_MT],
    0
) * 100

// 5. Best Performing Model MAE
Best_Model_MAE = 
MIN(ModelMetrics[MAE_tonnes])

// 6. Best Performing Model Name
Best_Model_Name = 
CALCULATE(
    FIRSTNONBLANK(ModelMetrics[Model], 1),
    FILTER(ModelMetrics, ModelMetrics[MAE_tonnes] = [Best_Model_MAE])
)

// 7. Gaussian Process 2030 Uncertainty Spread (Tonnes)
GP_2030_Uncertainty_Band = 
VAR HighVal = CALCULATE(SUM(ForecastResults[gp_95ci_high]), ForecastResults[financial_year] = "2030-31", ForecastResults[model] = "Gaussian Process")
VAR LowVal = CALCULATE(SUM(ForecastResults[gp_95ci_low]), ForecastResults[financial_year] = "2030-31", ForecastResults[model] = "Gaussian Process")
RETURN HighVal - LowVal
```

---

## 4. Dashboard Page Specifications

### Page 1 — E-Waste Overview
- **Header:** National E-Waste Generation Dynamics & Historical Baseline
- **Visuals:**
  1. **KPI Cards (Top Banner):**
     - Card 1: Latest Verified Generation (FY 2024–25): `1,397,956 MT` (~1.40 Mt).
     - Card 2: Peak Historical under 2016 Rules (FY 2022–23): `1,609,117 MT`.
     - Card 3: Regulatory Scope Transition: "21 EEE Categories (2016) → 106 Categories (2022 Rules)".
     - Card 4: Historical 5-Year CAGR (2017–2022): `17.8%`.
  2. **Stacked Column & Line Chart (Main Visual):**
     - X-Axis: `HistoricalData[financial_year]`
     - Column Values: `HistoricalData[ewaste_generated_tonnes]` (colored by `reporting_framework`).
     - Line Values: YoY Growth Rate (%)
     - Annotation: Methodology Break Flag between FY 2022–23 and FY 2023–24.
  3. **Table:** Source provenance matrix showing CPCB/PIB citations, publication dates, and verification status.

### Page 2 — Forecast Comparison
- **Header:** Multi-Model Generation Trajectories (2025–2030 Horizon)
- **Visuals:**
  1. **Slicer:** `ForecastResults[model]` (Multi-select: Naive, Linear Regression, Linear Regression (FW), ARIMA, Random Forest, XGBoost, Gaussian Process).
  2. **Line and Clustered Area Chart:**
     - X-Axis: `financial_year`
     - Historical Series: Solid Black line with round markers (`Actual (Historical)`).
     - Forecast Series: Dashed colored lines per model.
     - Area / Ribbon: `gp_95ci_low` to `gp_95ci_high` (Red transparent ribbon representing 95% Bayesian credible interval).
  3. **Matrix Visual:**
     - Rows: `financial_year`
     - Columns: `model`
     - Values: `forecast_tonnes`
     - Subtotal/Totals disabled.
  4. **Callout Call-out Banner:** Highlighting tree-model plateau behavior (RF/XGBoost saturation at ~1.43 Mt) vs linear extrapolation.

### Page 3 — Model Performance
- **Header:** Empirical Validation & Predictive Error Comparison
- **Visuals:**
  1. **Clustered Bar Chart:** MAE (Tonnes) by Model.
  2. **Clustered Bar Chart:** RMSE (Tonnes) by Model.
  3. **Clustered Bar Chart:** MAPE (%) and sMAPE (%) by Model.
  4. **Scatter Plot:** Prediction Residuals (Actual vs. Predicted across rolling-origin folds).
  5. **Summary Card:** Best overall empirical performer on rolling-origin backtesting: `Naive Baseline` (13.7% MAPE) / `ARIMA(1,1,0)` (15.5% MAPE) due to the sharp regulatory break.

### Page 4 — Model Reliability & Robustness
- **Header:** Stress Testing Under Data Scarcity & Perturbation
- **Visuals:**
  1. **Clustered Column Chart (Experiment A):** Training History Sensitivity (n=4 vs n=5 vs n=6).
  2. **Waterfall / Deviation Chart (Experiment B):** Impact of dropping single historical observations (Jackknife/Leave-One-Out).
  3. **Error Bar Chart (Experiment C):** Gaussian Noise Injection (5%, 10%, 20% noise variance over 20 Monte Carlo iterations).
  4. **Line Chart (Experiment D):** Standard deviation expansion of Gaussian Process across forecast horizons.

### Page 5 — Planning Insights & EIS Decision Support
- **Header:** Strategic Infrastructure Sizing & Enterprise Implications
- **Visuals:**
  1. **Recycling Capacity Gap Gauge:** Comparing forecasted 2030 generation (2.67 Mt under Linear FW) against current authorized formal dismantling/recycling capacity.
  2. **Scenario Matrix:** Low (ARIMA: 1.43 Mt), Moderate (LinReg: 2.26 Mt), High (LinReg FW: 2.67 Mt), International Benchmark (NITI/GEM: >10 Mt).
  3. **EPR Target Compliance Calculator:** Formal collection requirements based on MoEFCC targets (80% by 2027–28 onwards).
  4. **Executive Caveat Panel:** Explicit disclaimer on small-sample constraints, lack of granular state-level generation panels, and the risks of long-range extrapolation.

---

## 5. Step-by-Step Power BI Desktop Build Instructions

1. Open **Power BI Desktop**.
2. Click **Get Data** > **Text/CSV**, navigate to `outputs/power_bi/`, and import all 7 CSV files.
3. Ensure data types are detected correctly:
   - `financial_year`: Text
   - `fy_start`: Whole Number
   - `year_index`: Whole Number
   - All `_tonnes` and `_kt` fields: Decimal Number
   - `MAPE_pct`, `sMAPE_pct`: Decimal Number
4. Switch to **Model View** and verify relationships match the Star Schema defined in Section 2.
5. Create a new Table `_Measures` and copy the DAX measures from Section 3.
6. Create 5 Report Pages matching Section 4.
7. Save the report as `E-Waste_Forecasting_India.pbix`.

# Data Audit & Feasibility Assessment Report

**Project Title:** Comparative Analysis of Predictive Models for E-Waste Generation Forecasting in India  
**Subject:** Enterprise Information Systems (EIS)  
**Deliverable:** Phase 1 Formal Data Audit Report  
**Author:** EIS Project Team  

---

## 1. Executive Summary & Feasibility Assessment

This report provides the formal data quality audit and feasibility evaluation conducted on the raw institutional datasets available for the electronic waste (e-waste) forecasting project in India.

### Core Feasibility Question
> **Do we have enough comparable observations to conduct a defensible comparison of predictive models?**

### Definitive Answer
**Yes, but strictly under a constrained national time-series design (Approach A, $n=8$) with documented methodology flags.** 

The dataset is **not** large enough for unconstrained machine learning, deep neural networks, or complex panel econometric modeling. However, with appropriate chronological rolling-origin backtesting, robust regularized parameters, and an explicit binary indicator for the statutory regulatory transition from the *2016 Rules* to the *2022 Rules*, a scientifically valid, reproducible comparative study across 6 model families is feasible.

---

## 2. Inventory of Files & Worksheets Inspected

| File Name | Format | File Size | Primary Content | Inspected Sheets / Tables |
| :--- | :---: | :---: | :--- | :--- |
| `E-WASTE VALUE.xlsx` | Excel (.xlsx) | 16,831 bytes | National historical generation + State collection & generation extracts | 1. `E-WASTE INDIA`<br>2. `STATE WISE E-WASTE COLLECTION `<br>3. `STATE E-WASTE GENERATION(2018`<br>4. `STATE WISE WASTE GENERATION2023` |
| `EWaste_Forecasting_Master_Data.xlsx` | Excel (.xlsx) | 18,203 bytes | Official CPCB/PIB national series, metadata, source register, data quality checklist, and international benchmarks | 1. `Read Me`<br>2. `Master Data`<br>3. `Source Register`<br>4. `Data Quality`<br>5. `External Benchmarks` |
| `RS_Session_266_AU_2384_A.csv` | Delimited (.csv) | 133 bytes | Official parliamentary response table (Rajya Sabha Session 266, AU 2384) | Single table: Financial Year vs E-Waste Generation (Metric Ton) |

---

## 3. Detailed Worksheet-by-Worksheet Audit

### 3.1 `E-WASTE VALUE.xlsx`

#### Sheet 1: `E-WASTE INDIA`
- **Dimensions:** 7 rows $\times$ 2 columns.
- **Columns:** `YEARS`, `GENERATION (TONS)`.
- **Temporal Span:** FY 2016–17 to FY 2022–23.
- **Reported Values:**
  - `2016-17`: $23,330.30\text{ T}$
  - `2017-18`: $708,445.00\text{ T}$
  - `2018-19`: $771,215.00\text{ T}$
  - `2019-20`: $1,014,961.21\text{ T}$
  - `2020-21`: $1,346,496.31\text{ T}$
  - `2021-22`: $1,601,155.36\text{ T}$
  - `2022-23`: $1,609,117.00\text{ T}$
- **Audit Finding (CRITICAL DEFECT):** The FY 2016–17 figure ($23,330.3\text{ MT}$) is **not** e-waste generated; verification against CPCB annual reports and PIB releases confirms it is **e-waste collected/processed** through formal recyclers. Including it creates an artificial 30-fold increase into 2017–18. **Action:** Excluded from generation modeling.

#### Sheet 2: `STATE WISE E-WASTE COLLECTION `
- **Dimensions:** 35 rows $\times$ 5 columns.
- **Columns:** `SL NO.`, `Name of the State`, `E-Waste collected & processed in tonnes` (FY 2019–20, FY 2020–21, FY 2021–22).
- **Audit Finding:** Contains formal collection and processing data, **not** generation data. While valuable for downstream logistics and recycling capacity planning, it cannot serve as the dependent target variable for e-waste generation forecasting.

#### Sheet 3: `STATE E-WASTE GENERATION(2018`
- **Dimensions:** 13 rows $\times$ 3 columns.
- **Columns:** `STATE`, `E-WASTE GENERATION(Ton) [2018]`, `E-WASTE GENERATION(Ton) [2023]`.
- **Data Quality Issues:**
  - Non-breaking spaces and formatting corruption in numeric cells (e.g. Delhi 2023: `'\xa0200,000\xa0'`; West Bengal 2023: `'320.44\xa0'`).
  - Missing value for Punjab 2023 (`None`).
  - Restricts coverage to top 10 states only (omits 25+ states/UTs).
  - Ambiguous time basis (calendar year vs financial year unstated).
- **Audit Finding:** Incomplete and noisy cross-sectional snapshot; unusable for rigorous multi-year panel modeling.

#### Sheet 4: `STATE WISE WASTE GENERATION2023`
- **Dimensions:** 35 rows $\times$ 4 columns.
- **Columns:** `Sl. No.`, `State/UT`, `Waste Generation (in TPD)`, `Waste Processed (in TPD)`.
- **Audit Finding (CRITICAL DEFECT):** Reported in **TPD (Tonnes Per Day)**. The figures represent **Municipal Solid Waste (MSW)**, not electronic waste (e.g., Delhi: 10,181 TPD = ~3.7 million tonnes/year, far exceeding all e-waste in India). **Action:** Excluded from e-waste modeling.

---

### 3.2 `EWaste_Forecasting_Master_Data.xlsx`

#### Sheet: `Master Data`
- **Dimensions:** 9 rows $\times$ 16 columns.
- **Metadata Fields:** `Record ID`, `Financial Year`, `Period Basis`, `Geography`, `Metric`, `Value (tonnes)`, `Value (kt)`, `Data Status`, `Reporting Framework`, `Comparability Group`, `Source ID`, `Source URL`.
- **Temporal Span:** FY 2017–18 to FY 2024–25.
- **Audit Finding (Data Gap Identified):** Record `IN006` (FY 2022–23) was left unpopulated (`NaN`). Resolved by verifying parliamentary replies and CPCB submissions, populating $1,609,117.00\text{ MT}$.

#### Sheet: `External Benchmarks`
- Contains international benchmarks from Global E-waste Monitor (GEM 2024: $4,137\text{ kt}$ for CY 2022) and NITI Aayog citations ($2,760\text{ kt}$ for 2020; $6,190\text{ kt}$ for 2024; $14,000\text{ kt}$ for 2030).
- **Audit Finding:** Documented strictly as validation benchmarks. They must **never** be merged directly into CPCB training data because GEM uses consumption/MFA models tracking all electronics, whereas CPCB tracks formal EPR producer sales.

---

### 3.3 `RS_Session_266_AU_2384_A.csv`
- **Dimensions:** 5 rows $\times$ 2 columns.
- **Temporal Span:** FY 2019–20 to FY 2023–24.
- **Discrepancy Detected:** Reports FY 2023–24 as $1,751,236\text{ MT}$, whereas the official MoEFCC audited release (PIB PRID: 2147876) reports $1,254,286.55\text{ MT}$ under the 2022 Rules. The PIB audited figure was adopted for consistency with FY 2024–25 ($1,397,955.59\text{ MT}$).

---

## 4. Cross-Source Comparison Matrix

| Financial Year | `E-WASTE VALUE.xlsx` (India) | `EWaste Master Data` | `RS_Session CSV` | Final Verified Value | Audit Status & Resolution |
| :---: | :---: | :---: | :---: | :---: | :--- |
| **2016–17** | 23,330.3 MT | Unlisted | Unlisted | **Excluded** | Confirmed formal collection, NOT generation. |
| **2017–18** | 708,445 MT | 708,445 MT | Unlisted | **708,445.00 MT** | Full consensus across official sources. |
| **2018–19** | 771,215 MT | 771,215 MT | Unlisted | **771,215.00 MT** | Full consensus across official sources. |
| **2019–20** | 1,014,961.21 MT | 1,014,961.21 MT | 1,014,961 MT | **1,014,961.21 MT** | Full consensus (rounding in CSV). |
| **2020–21** | 1,346,496.31 MT | 1,346,496.31 MT | 1,346,496 MT | **1,346,496.31 MT** | Full consensus (rounding in CSV). |
| **2021–22** | 1,601,155.36 MT | 1,601,155.36 MT | 1,601,155 MT | **1,601,155.36 MT** | Full consensus (rounding in CSV). |
| **2022–23** | 1,609,117 MT | `NaN` (Gap) | 1,609,117 MT | **1,609,117.00 MT** | Gap resolved via parliamentary answer. |
| **2023–24** | Unlisted | 1,254,286.55 MT | 1,751,236 MT | **1,254,286.55 MT** | PIB S02 audited portal figure adopted. |
| **2024–25** | Unlisted | 1,397,955.59 MT | Unlisted | **1,397,955.59 MT** | PIB S02 audited portal figure adopted. |

---

## 5. Changes in Statutory Measurement Methodology

A pivotal contribution of this audit is documenting the structural regime change in Indian environmental accounting:

```
2016 Rules Regime (FY 2017-18 to FY 2022-23)         2022 Rules Regime (FY 2023-24 onwards)
┌──────────────────────────────────────────────┐     ┌──────────────────────────────────────────────┐
│ • Scope: 21 notified EEE categories          │     │ • Scope: 106 notified EEE categories         │
│ • Producer sales + standard lifespan         │ ──► │ • Centralized EPR Portal sales registration  │
│ • Generation grew: 708k MT to 1,609k MT      │     │ • Generation: 1,254k MT to 1,398k MT         │
└──────────────────────────────────────────────┘     └──────────────────────────────────────────────┘
                                          ▲
                                          │
                               Methodology Shift
                           (Not physical reduction)
```

1. **2016 Rules:** 21 EEE types. Producer declarations compiled manually across SPCBs.
2. **2022 Rules (effective April 1, 2023):** 106 EEE types. Required all producers to register and upload sales on the centralized online CPCB EPR portal. Because portal onboarding was progressive, initial reported totals in FY 2023–24 were lower ($1.25\text{ M MT}$ vs $1.61\text{ M MT}$).
3. **Analytical Treatment:** Models that fail to account for this step-down treat it as negative growth, leading to erroneous downward forecasts. We introduced a binary variable `framework_flag` ($0$ for pre-2023, $1$ for post-2023) to preserve continuity without distorting growth rates.

---

## 6. Selection of Modeling Approach: Approach A vs. Approach B

### Approach B: State-Year Panel Modeling — REJECTED
- **Rationale for Rejection:**
  1. The accessible state-level data (`STATE WISE E-WASTE COLLECTION `) tracks formal processing, not generation.
  2. The generation sheet (`STATE E-WASTE GENERATION(2018`) covers only two isolated years (2018 and 2023) for only 10 states, with multiple corrupted cells.
  3. Manufacturing state-year observations would violate academic ethics and fabricate synthetic data.

### Approach A: National Time-Series Modeling — SELECTED & APPROVED
- **Rationale for Selection:**
  1. 8 verified, authoritative annual national observations (FY 2017–18 through FY 2024–25).
  2. Complete source provenance linking to parliamentary records and official MoEFCC releases.
  3. Supports rigorous chronological backtesting across 4 expanding-window origins ($k \in \{4, 5, 6, 7\}$).
  4. Directly aligns with the project title: *Comparative Analysis of Predictive Models for E-Waste Generation Forecasting in India*.

---

## 7. Model Candidacy & Technical Constraints

Given $n=8$ national observations:
- **Naive Baseline:** Fully supported. Mandatory benchmark.
- **Linear Regression (OLS):** Fully supported. Minimal parameters ($p=2$ or $p=3$ with framework flag).
- **ARIMA(1,1,0):** Marginally supported. Feasible with low-order differencing ($d=1$) and single autoregressive lag.
- **Random Forest Regressor:** Constrained. Highly prone to overfitting; tree depth restricted ($\text{depth} \le 2$). Incapable of out-of-sample trend extrapolation.
- **XGBoost Regressor:** Constrained. Requires heavy L1/L2 regularization ($\alpha=1.0, \lambda=1.0$). Incapable of out-of-sample trend extrapolation.
- **Gaussian Process Regression:** Supported. Nonparametric Bayesian formulation with RBF + WhiteKernel. Provides valuable quantification of predictive uncertainty.

---

## 8. Conclusion & Sign-Off

The data audit confirms that a rigorous, reproducible, and defensible comparative modeling study is fully achievable using the verified 8-year national time series with statutory framework controls. Proceeding to model training and evaluation is approved.

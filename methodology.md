# Methodology Document

**Project Title:** Comparative Analysis of Predictive Models for E-Waste Generation Forecasting in India  
**Course:** Enterprise Information Systems (EIS)  

---

## 1. Problem Formulation & Academic Motivation

Enterprise Information Systems (EIS) transform fragmented operational data into structured predictive intelligence to support long-term capital allocation, logistics planning, and environmental compliance. In the context of India's electronic waste (e-waste) management ecosystem, state agencies, Extended Producer Responsibility (EPR) compliance bodies, and commercial recycling operators require reliable forecasts of future e-waste generation to size dismantling facilities and design collection infrastructure.

However, developing economies face severe data scarcity. In India, official annual national e-waste generation figures are derived from statutory Extended Producer Responsibility filings under shifting regulatory frameworks rather than direct physical mass measurements.

### Primary Research Contribution
This study delivers a **comparative evaluation of forecasting-model accuracy, stability, and extrapolation validity under limited-data ($n=8$) and structural-break conditions**.

---

## 2. Statutory Data Audit & Accounting Boundary Discrepancies

### 2.1 The Official Indian Estimation Protocol
The Central Pollution Control Board (CPCB) estimates national e-waste generation using an **End-of-Life (EoL) Sales-Lifespan Model**:

$$\text{Generation}_{(x-y)} = \text{Sales of EEE in Financial Year } ((x-z) - (y-z))$$

where:
- $(x-y)$ is the target financial year (e.g. 2021–22),
- $z$ is the statutory average lifespan assigned to each notified Electrical and Electronic Equipment (EEE) product category (e.g. Mainframes = 10 years; Personal Computers = 6 years; Cellular Phones = 5 years).

### 2.2 The Regulatory Structural Break
A critical finding of our data audit is that the CPCB historical series is **not continuous**:
1. **The 2016 Rules Era (FY 2017–18 through FY 2022–23):** E-waste generation was estimated across **21 notified EEE item categories** under the *E-Waste (Management) Rules, 2016*. Generation grew from $708,445\text{ MT}$ to $1,609,117\text{ MT}$.
2. **The 2022 Rules Era (Effective April 1, 2023 / FY 2023–24 onwards):** The *E-Waste (Management) Rules, 2022* superseded the 2016 Rules, dramatically expanding the statutory schedule to **106 EEE product categories** while restricting estimation strictly to sales reported by registered producers on the centralized online EPR Portal. Consequently, the reported generation for FY 2023–24 dropped to $1,254,286.55\text{ MT}$ before rising to $1,397,955.59\text{ MT}$ in FY 2024–25.

> **Data Quality Rule:** This drop of $-22.05\%$ between FY 2022–23 and FY 2023–24 does not reflect a physical collapse in electronic equipment disposal; rather, it reflects a **measurement and reporting methodology break**. Merging these regimes without an indicator variable introduces artificial volatility into time-series models.

### 2.3 Exclusion of Erroneous & Non-Generation Records
- **2016–17 Record ($23,330.3\text{ MT}$):** Found in `E-WASTE VALUE.xlsx`. Cross-validation with PIB and Lok Sabha records proves this represents **formally collected/processed e-waste**, not generated e-waste. It was excluded from the generation modeling pipeline.
- **State-Level Solid Waste Sheet:** The sheet `STATE WISE WASTE GENERATION2023` in `E-WASTE VALUE.xlsx` reports figures in "Tonnes Per Day (TPD)" for 35 states/UTs. These figures correspond to municipal solid waste, not e-waste, and were excluded.
- **State-Level Collection Sheet:** Represents formal processing volumes across 35 states for 3 years, not state-level generation.

---

## 3. Modeling Methodology & Mathematical Specifications

We evaluate six candidate models representing distinct algorithmic paradigms:

### Model 1: Naive Random-Walk Baseline
$$\hat{y}_{t+h|t} = y_t$$
Serves as the benchmark. In non-stationary series with structural breaks, a naive model frequently penalizes overfitted complex models.

### Model 2: Linear Trend Regression
Two variants are specified via Ordinary Least Squares (OLS):
- **Standard Linear Trend:**
  $$\hat{y}_t = \beta_0 + \beta_1 t$$
- **Framework-Adjusted Linear Trend:**
  $$\hat{y}_t = \beta_0 + \beta_1 t + \beta_2 D_t^{\text{2022}}$$
  where $D_t^{\text{2022}} \in \{0, 1\}$ is a binary indicator encoding the regulatory shift effective FY 2023–24.

### Model 3: Autoregressive Integrated Moving Average — ARIMA(1, 1, 0)
First-difference autoregressive formulation:
$$(1 - \phi_1 B)(1 - B) y_t = \epsilon_t \implies \Delta y_t = \phi_1 \Delta y_{t-1} + \epsilon_t$$
Parameters are estimated via Maximum Likelihood on the differenced stationary series.

### Model 4: Random Forest Regressor
Ensemble of shallow bagged decision trees ($B = 50$, $\text{max\_depth} = 2$, $\text{min\_samples\_split} = 3$):
$$\hat{y}(x) = \frac{1}{B} \sum_{b=1}^B T_b(x)$$
Regularized to mitigate extreme overfitting on $n=8$.

### Model 5: XGBoost Regressor
Gradient-boosted decision trees minimizing regularized objective:
$$\mathcal{L} = \sum_{i} l(y_i, \hat{y}_i) + \sum_k \left( \gamma T + \frac{1}{2} \lambda \|w\|^2 + \alpha |w| \right)$$
Configured with $L_1$ ($\alpha=1.0$) and $L_2$ ($\lambda=1.0$) penalties to prevent tree memorization.

### Model 6: Gaussian Process Regression (GPR)
Bayesian nonparametric prior over functions:
$$f(x) \sim \mathcal{GP}\left(m(x), k(x, x')\right)$$
with a composite kernel consisting of a Constant Kernel, Radial Basis Function (RBF), and White Noise Kernel:
$$k(x, x') = \sigma_f^2 \exp\left(-\frac{(x - x')^2}{2 l^2}\right) + \sigma_n^2 \delta_{x, x'}$$
The predictive distribution at test input $x_*$ is Gaussian:
$$y_* \mid X, y, x_* \sim \mathcal{N}(\mu_*, \sigma_*^2)$$

---

## 4. Evaluation Strategy: Rolling-Origin Backtesting

Because standard $k$-fold cross-validation and random train/test splits destroy temporal ordering and cause lookahead leakage, we implement **chronological rolling-origin evaluation** across 4 expanding windows:

| Fold Origin ($k$) | Training Indices | Training Period | Forecast Target | Target Financial Year |
| :---: | :---: | :---: | :---: | :---: |
| 1 | $1 \dots 4$ | FY 2017–18 to FY 2020–21 | Fold 5 | FY 2021–22 |
| 2 | $1 \dots 5$ | FY 2017–18 to FY 2021–22 | Fold 6 | FY 2022–23 |
| 3 | $1 \dots 6$ | FY 2017–18 to FY 2022–23 | Fold 7 | FY 2023–24 (Methodology break) |
| 4 | $1 \dots 7$ | FY 2017–18 to FY 2023–24 | Fold 8 | FY 2024–25 |

### Statistical Metrics
1. **Mean Absolute Error (MAE):** $\text{MAE} = \frac{1}{N}\sum_{i=1}^N |y_i - \hat{y}_i|$
2. **Root Mean Squared Error (RMSE):** $\text{RMSE} = \sqrt{\frac{1}{N}\sum_{i=1}^N (y_i - \hat{y}_i)^2}$
3. **Mean Absolute Percentage Error (MAPE):** $\text{MAPE} = \frac{1}{N}\sum_{i=1}^N \left|\frac{y_i - \hat{y}_i}{y_i}\right| \times 100\%$
4. **Symmetric MAPE (sMAPE):** $\text{sMAPE} = \frac{1}{N}\sum_{i=1}^N \frac{|y_i - \hat{y}_i|}{(|y_i| + |\hat{y}_i|)/2} \times 100\%$

---

## 5. Robustness & Stability Stress-Testing Framework

To address the core research objective under limited data, four controlled experiments were conducted:
- **Experiment A (Sample Size Sensitivity):** Evaluates performance when training history is truncated from $n=6$ to $n=5$ and $n=4$.
- **Experiment B (Jackknife / Drop-One Resilience):** Systematically removes one historical observation from the training fold to identify high-leverage data points.
- **Experiment C (Measurement Noise Injection):** Injects zero-mean Gaussian perturbations ($\sigma \in \{5\%, 10\%, 20\%\}$) over 20 Monte Carlo iterations.
- **Experiment D (Uncertainty Quantification):** Analyzes the variance expansion of the Gaussian Process predictive distribution over a 6-year forecast horizon.

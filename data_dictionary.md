# Data Dictionary

**Project Title:** Comparative Analysis of Predictive Models for E-Waste Generation Forecasting in India  
**Course:** Enterprise Information Systems (EIS)  

---

## 1. Verified National Dataset (`data/processed/national_ewaste_full.csv` & `outputs/power_bi/historical_data.csv`)

| Column Name | Data Type | Unit | Description | Range / Values |
| :--- | :--- | :--- | :--- | :--- |
| `financial_year` | String | N/A | Official Indian financial year (April 1 to March 31). | `2017-18` to `2024-25` |
| `fy_start` | Integer | Year | The calendar year in which the financial year commences. | `2017` to `2024` |
| `year_index` | Integer | Ordinal | Ordinal integer time index (1 = first observation). | `1` to `8` |
| `years_since_start` | Integer | Years | Continuous elapsed time counter from baseline. | `0` to `7` |
| `ewaste_generated_tonnes` | Float | Tonnes (MT) | National e-waste generation quantity in metric tonnes as estimated by CPCB. | `708,445.00` to `1,609,117.00` |
| `ewaste_generated_kt` | Float | Kilotonnes | Generation in kilotonnes ($1\text{ kt} = 1,000\text{ MT}$). | `708.445` to `1,609.117` |
| `framework_flag` | Binary | $\{0, 1\}$ | Indicator variable for regulatory framework change: `0` = 2016 Rules, `1` = 2022 Rules. | `0`, `1` |
| `reporting_framework` | String | N/A | Title of statutory framework under which calculation occurred. | `2016 Rules`, `2022 Rules` |
| `comparability_group` | String | N/A | Internal code segmenting observations by continuous reporting method. | `CPCB_2016`, `CPCB_2022` |
| `source_id` | String | ID | Foreign key to `source_register.csv`. | `S01`, `S02`, `S_RS` |
| `record_id` | String | ID | Unique alphanumeric identifier for observation. | `IN001` to `IN008` |
| `yoy_growth_pct` | Float | Percentage | Year-over-year percentage change in generation. | $-22.05\%$ to $+32.66\%$ |

---

## 2. Multi-Model Forecasts (`outputs/power_bi/forecast_results.csv`)

| Column Name | Data Type | Unit | Description | Range / Values |
| :--- | :--- | :--- | :--- | :--- |
| `financial_year` | String | N/A | Financial year of forecast or historical anchor. | `2017-18` to `2030-31` |
| `fy_start` | Integer | Year | Starting calendar year. | `2017` to `2030` |
| `model` | String | N/A | Name of model generating projection or `Actual (Historical)`. | 7 categories |
| `forecast_tonnes` | Float | Tonnes (MT) | Predicted or actual e-waste generated in metric tonnes. | Positive float |
| `forecast_kt` | Float | Kilotonnes | Predicted or actual e-waste generated in kilotonnes. | Positive float |
| `is_forecast` | Boolean | N/A | `True` for model projections; `False` for verified historical actuals. | `True`, `False` |
| `forecast_horizon_years` | Integer | Years | Step ahead from last historical observation ($0$ for actuals). | `0` to `6` |
| `gp_std` | Float | Tonnes (MT) | Predictive standard deviation from Gaussian Process Regression. | $\ge 0$ (GP only) |
| `gp_95ci_low` | Float | Tonnes (MT) | Lower bound of 95% Bayesian credible interval ($\mu - 1.96\sigma$). | Float (GP only) |
| `gp_95ci_high` | Float | Tonnes (MT) | Upper bound of 95% Bayesian credible interval ($\mu + 1.96\sigma$). | Float (GP only) |

---

## 3. Evaluation Metrics (`outputs/power_bi/model_metrics.csv`)

| Column Name | Data Type | Unit | Description |
| :--- | :--- | :--- | :--- |
| `Model` | String | N/A | Name of statistical or machine learning model. |
| `Eval_Method` | String | N/A | Cross-validation design (`Rolling-Origin (4 windows)`). |
| `N_Test_Obs` | Integer | Count | Number of out-of-sample one-step-ahead test evaluation points ($4$). |
| `MAE_tonnes` | Float | Tonnes (MT) | Mean Absolute Error across chronological validation windows. |
| `RMSE_tonnes` | Float | Tonnes (MT) | Root Mean Squared Error across chronological validation windows. |
| `MAPE_pct` | Float | Percentage | Mean Absolute Percentage Error ($\frac{1}{n}\sum |\frac{y - \hat{y}}{y}| \times 100$). |
| `sMAPE_pct` | Float | Percentage | Symmetric Mean Absolute Percentage Error. |

---

## 4. Robustness & Sensitivity Metrics (`outputs/power_bi/model_robustness_results.csv`)

| Column Name | Data Type | Unit | Description |
| :--- | :--- | :--- | :--- |
| `experiment` | String | N/A | Experiment identifier: `A_limited_training`, `B_missing_obs`, `C_noise`, `D_uncertainty`. |
| `model` | String | N/A | Model tested under perturbation. |
| `config` | String | N/A | Experimental setup parameter (e.g. `Full (n=6)`, `Drop 2020-21`, `10% Gaussian noise`). |
| `train_n` | Integer | Count | Number of training observations in fold. |
| `test_n` | Integer | Count | Number of holdout test observations. |
| `MAE_tonnes` | Float | Tonnes (MT) | Test MAE under perturbed condition. |
| `RMSE_tonnes` | Float | Tonnes (MT) | Test RMSE or standard deviation of Monte Carlo MAE. |
| `MAPE_pct` | Float | Percentage | Holdout MAPE under perturbed condition. |

---

## 5. Source Register (`outputs/power_bi/source_register.csv` & root `source_register.csv`)

| Column Name | Data Type | Description |
| :--- | :--- | :--- |
| `Source_ID` | String | Unique source key (`S01`, `S02`, `S03`, `S04`, `S_RS`, `S_ParliVerify`). |
| `Publication` | String | Full title of official release, parliamentary question, or dataset. |
| `Type` | String | Category: `Official government release`, `Parliamentary record`, `International benchmark`. |
| `Coverage` | String | Year and geographic span covered. |
| `Variable` | String | Target indicator measured. |
| `Unit` | String | Unit reported in raw document. |
| `Framework` | String | Regulatory regime or accounting basis. |
| `URL` | String | Official source hyperlink. |

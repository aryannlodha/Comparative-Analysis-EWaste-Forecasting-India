"""
03_train_evaluate_forecast.py
=============================
Phases 3-6: Model Training, Evaluation, Robustness Testing, and Forecasting
Project: Comparative Analysis of Predictive Models for E-Waste Generation Forecasting in India

Models implemented:
  1. Naive Baseline (last-value-carried-forward)
  2. Linear Regression (OLS trend)
  3. ARIMA (low-order autoregressive integrated moving average)
  4. Random Forest Regression (ensemble, with heavy caveats)
  5. XGBoost Regression (gradient boosting, with heavy caveats)
  6. Gaussian Process Regression (Bayesian nonparametric)
"""

import os
import sys
import time
import warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, ConstantKernel, WhiteKernel
from sklearn.metrics import mean_absolute_error, root_mean_squared_error
from statsmodels.tsa.arima.model import ARIMA
import xgboost as xgb

warnings.filterwarnings('ignore')
np.random.seed(42)

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROCESSED_DIR = os.path.join(PROJECT_DIR, 'data', 'processed')
FIGURES_DIR = os.path.join(PROJECT_DIR, 'outputs', 'figures')
RESULTS_DIR = os.path.join(PROJECT_DIR, 'outputs', 'model_results')
PBI_DIR = os.path.join(PROJECT_DIR, 'outputs', 'power_bi')
REPORTS_DIR = os.path.join(PROJECT_DIR, 'outputs', 'reports')
for d in [FIGURES_DIR, RESULTS_DIR, PBI_DIR, REPORTS_DIR]:
    os.makedirs(d, exist_ok=True)

print("=" * 80)
print("PHASES 3-6: MODEL TRAINING, EVALUATION, ROBUSTNESS, AND FORECASTING")
print("=" * 80)

# ============================================================================
# LOAD DATA
# ============================================================================
df = pd.read_csv(os.path.join(PROCESSED_DIR, 'national_ewaste_full.csv'))
print(f"\nLoaded dataset: {len(df)} observations")
print(df[['financial_year', 'ewaste_generated_tonnes', 'reporting_framework']].to_string(index=False))

y_all = df['ewaste_generated_tonnes'].values
X_all = df['year_index'].values.reshape(-1, 1)
fw_flag = df['framework_flag'].values
X_all_with_fw = np.column_stack([X_all, fw_flag])


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================
def calc_mape(y_true, y_pred):
    """Mean Absolute Percentage Error"""
    y_true = np.array(y_true, dtype=float)
    y_pred = np.array(y_pred, dtype=float)
    mask = y_true != 0
    return np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100


def calc_smape(y_true, y_pred):
    """Symmetric Mean Absolute Percentage Error"""
    y_true = np.array(y_true, dtype=float)
    y_pred = np.array(y_pred, dtype=float)
    denom = (np.abs(y_true) + np.abs(y_pred)) / 2
    mask = denom != 0
    return np.mean(np.abs(y_true[mask] - y_pred[mask]) / denom[mask]) * 100


# ============================================================================
# PHASE 3: MODEL DEFINITIONS
# ============================================================================
print("\n" + "=" * 80)
print("PHASE 3: MODEL TRAINING")
print("=" * 80)


class NaiveModel:
    """Naive baseline: forecast = last observed value"""
    def __init__(self):
        self.last_value = None
        self.name = "Naive Baseline"

    def fit(self, X, y):
        self.last_value = y[-1]

    def predict(self, X):
        return np.full(len(X), self.last_value)

    def description(self):
        return {
            'name': self.name,
            'how_it_works': 'Uses the most recent observed value as forecast for all future periods',
            'why_included': 'Establishes minimum benchmark; any useful model must beat this',
            'assumptions': 'Time series is a random walk (no trend, no seasonality)',
            'limitations': 'Cannot capture trends, growth, or structural changes',
            'input_variables': 'Only the last observation',
            'training_method': 'Store last value',
            'validation_method': 'Chronological holdout'
        }


class LinearRegressionModel:
    """Linear trend model: y = a + b*t"""
    def __init__(self, use_framework_flag=False):
        self.model = LinearRegression()
        self.use_fw = use_framework_flag
        self.name = "Linear Regression" + (" (with framework flag)" if use_framework_flag else "")

    def fit(self, X, y, fw=None):
        if self.use_fw and fw is not None:
            X_train = np.column_stack([X, fw])
        else:
            X_train = X.reshape(-1, 1) if X.ndim == 1 else X
        self.model.fit(X_train, y)

    def predict(self, X, fw=None):
        if self.use_fw and fw is not None:
            X_pred = np.column_stack([X, fw])
        else:
            X_pred = X.reshape(-1, 1) if X.ndim == 1 else X
        return self.model.predict(X_pred)

    def description(self):
        return {
            'name': self.name,
            'how_it_works': 'Fits y = a + b*time (+ c*framework_flag) via OLS',
            'why_included': 'Tests whether a simple linear trend explains the data',
            'assumptions': 'Linear relationship between time and e-waste; constant variance; independent errors',
            'limitations': 'Cannot capture acceleration, saturation, or nonlinear patterns',
            'input_variables': 'year_index' + (', framework_flag' if self.use_fw else ''),
            'training_method': 'Ordinary Least Squares',
            'validation_method': 'Chronological holdout'
        }


class ARIMAModel:
    """ARIMA model for time series forecasting"""
    def __init__(self, order=(1, 1, 0)):
        self.order = order
        self.model = None
        self.fitted = None
        self.name = f"ARIMA{order}"

    def fit(self, X, y):
        self.train_y = y.copy()
        self.model = ARIMA(y, order=self.order)
        self.fitted = self.model.fit()

    def predict(self, n_steps):
        forecast = self.fitted.forecast(steps=n_steps)
        return forecast

    def description(self):
        return {
            'name': self.name,
            'how_it_works': f'ARIMA(p={self.order[0]},d={self.order[1]},q={self.order[2]}): '
                           f'autoregressive with {self.order[1]}-order differencing',
            'why_included': 'Captures temporal dependence and trend via differencing',
            'assumptions': 'Stationary after differencing; homoscedastic errors',
            'limitations': f'Only {len(self.train_y) if hasattr(self, "train_y") else "?"} observations; '
                          f'very limited for reliable parameter estimation',
            'input_variables': 'Time series values only (no external regressors)',
            'training_method': 'Maximum Likelihood Estimation',
            'validation_method': 'Chronological holdout'
        }


class RandomForestModel:
    """Random Forest with heavy regularization for small datasets"""
    def __init__(self, use_framework_flag=False):
        self.model = RandomForestRegressor(
            n_estimators=50, max_depth=2, min_samples_split=3,
            min_samples_leaf=2, random_state=42
        )
        self.use_fw = use_framework_flag
        self.name = "Random Forest"

    def fit(self, X, y, fw=None):
        if self.use_fw and fw is not None:
            X_train = np.column_stack([X, fw])
        else:
            X_train = X.reshape(-1, 1) if X.ndim == 1 else X
        self.model.fit(X_train, y)

    def predict(self, X, fw=None):
        if self.use_fw and fw is not None:
            X_pred = np.column_stack([X, fw])
        else:
            X_pred = X.reshape(-1, 1) if X.ndim == 1 else X
        return self.model.predict(X_pred)

    def description(self):
        return {
            'name': self.name,
            'how_it_works': 'Ensemble of shallow decision trees averaging predictions',
            'why_included': 'Tests whether nonlinear patterns improve forecasting',
            'assumptions': 'Features capture relevant patterns; enough data for tree splits',
            'limitations': 'SEVERE: Only 8 observations; max_depth=2 and min_samples heavily constrained; '
                          'cannot extrapolate beyond training range (RF predictions plateau for future years)',
            'input_variables': 'year_index' + (', framework_flag' if self.use_fw else ''),
            'training_method': 'Bagged ensemble of constrained trees (seed=42)',
            'validation_method': 'Chronological holdout'
        }


class XGBoostModel:
    """XGBoost with heavy regularization"""
    def __init__(self, use_framework_flag=False):
        self.model = xgb.XGBRegressor(
            n_estimators=30, max_depth=2, learning_rate=0.1,
            min_child_weight=3, reg_alpha=1.0, reg_lambda=1.0,
            random_state=42, verbosity=0
        )
        self.use_fw = use_framework_flag
        self.name = "XGBoost"

    def fit(self, X, y, fw=None):
        if self.use_fw and fw is not None:
            X_train = np.column_stack([X, fw])
        else:
            X_train = X.reshape(-1, 1) if X.ndim == 1 else X
        self.model.fit(X_train, y)

    def predict(self, X, fw=None):
        if self.use_fw and fw is not None:
            X_pred = np.column_stack([X, fw])
        else:
            X_pred = X.reshape(-1, 1) if X.ndim == 1 else X
        return self.model.predict(X_pred)

    def description(self):
        return {
            'name': self.name,
            'how_it_works': 'Gradient-boosted trees that sequentially correct errors',
            'why_included': 'Tests whether boosting improves over random forest',
            'assumptions': 'Enough data for meaningful gradient steps; features are informative',
            'limitations': 'SEVERE: Same extrapolation limitation as RF with only 8 observations; '
                          'heavy regularization applied to prevent overfitting',
            'input_variables': 'year_index' + (', framework_flag' if self.use_fw else ''),
            'training_method': 'Gradient boosting with L1/L2 regularization (seed=42)',
            'validation_method': 'Chronological holdout'
        }


class GaussianProcessModel:
    """Gaussian Process Regression with RBF kernel"""
    def __init__(self, use_framework_flag=False):
        kernel = ConstantKernel(1e12, (1e8, 1e16)) * RBF(2.0, (0.5, 10.0)) + WhiteKernel(1e8, (1e4, 1e12))
        self.model = GaussianProcessRegressor(
            kernel=kernel, n_restarts_optimizer=10, random_state=42, alpha=0
        )
        self.use_fw = use_framework_flag
        self.name = "Gaussian Process"

    def fit(self, X, y, fw=None):
        if self.use_fw and fw is not None:
            X_train = np.column_stack([X, fw])
        else:
            X_train = X.reshape(-1, 1) if X.ndim == 1 else X
        self.model.fit(X_train, y)

    def predict(self, X, fw=None, return_std=False):
        if self.use_fw and fw is not None:
            X_pred = np.column_stack([X, fw])
        else:
            X_pred = X.reshape(-1, 1) if X.ndim == 1 else X
        if return_std:
            return self.model.predict(X_pred, return_std=True)
        return self.model.predict(X_pred)

    def description(self):
        return {
            'name': self.name,
            'how_it_works': 'Bayesian nonparametric regression with RBF kernel; '
                           'provides mean prediction and uncertainty (standard deviation)',
            'why_included': 'Naturally provides prediction uncertainty estimates',
            'assumptions': 'Smooth underlying function; Gaussian noise',
            'limitations': 'Small dataset means wide uncertainty bands; '
                          'kernel hyperparameters may be poorly identified',
            'input_variables': 'year_index' + (', framework_flag' if self.use_fw else ''),
            'training_method': 'Marginal likelihood optimization (seed=42)',
            'validation_method': 'Chronological holdout'
        }


# ============================================================================
# PHASE 4: EVALUATION — ROLLING-ORIGIN CROSS-VALIDATION
# ============================================================================
print("\n" + "=" * 80)
print("PHASE 4: MODEL EVALUATION (Rolling-Origin)")
print("=" * 80)

results = []
all_predictions = []

# Rolling-origin: train on 1..k, predict k+1 (for k = 4,5,6,7)
min_train = 4
n = len(y_all)

for model_class, use_fw, model_label in [
    (NaiveModel, False, 'Naive Baseline'),
    (LinearRegressionModel, False, 'Linear Regression'),
    (LinearRegressionModel, True, 'Linear Regression (FW)'),
    (RandomForestModel, True, 'Random Forest'),
    (XGBoostModel, True, 'XGBoost'),
    (GaussianProcessModel, False, 'Gaussian Process'),
]:
    print(f"\n--- {model_label} ---")
    y_trues = []
    y_preds = []
    origins = []

    for k in range(min_train, n):
        X_tr = X_all[:k].flatten()
        y_tr = y_all[:k]
        fw_tr = fw_flag[:k]

        X_te = X_all[k:k+1].flatten()
        y_te = y_all[k]
        fw_te = fw_flag[k:k+1]

        if model_label == 'Naive Baseline':
            model = model_class()
            model.fit(X_tr, y_tr)
            pred = model.predict(X_te)
        elif 'ARIMA' in model_label:
            pass  # handled separately below
        else:
            model = model_class(use_framework_flag=use_fw)
            model.fit(X_tr, y_tr, fw=fw_tr)
            pred = model.predict(X_te, fw=fw_te)

        y_trues.append(y_te)
        y_preds.append(pred[0])
        origins.append(k)

        print(f"  Origin {k}: Train n={k}, Predict FY {df.iloc[k]['financial_year']}: "
              f"Actual={y_te:,.0f}  Predicted={pred[0]:,.0f}  Error={abs(y_te-pred[0]):,.0f}")

        all_predictions.append({
            'model': model_label,
            'eval_method': 'rolling_origin',
            'train_size': k,
            'test_fy': df.iloc[k]['financial_year'],
            'actual': y_te,
            'predicted': pred[0],
            'error': y_te - pred[0],
            'abs_error': abs(y_te - pred[0])
        })

    mae = mean_absolute_error(y_trues, y_preds)
    rmse = root_mean_squared_error(y_trues, y_preds)
    mape = calc_mape(y_trues, y_preds)
    smape = calc_smape(y_trues, y_preds)

    print(f"  MAE:  {mae:,.0f} tonnes")
    print(f"  RMSE: {rmse:,.0f} tonnes")
    print(f"  MAPE: {mape:.1f}%")
    print(f"  sMAPE: {smape:.1f}%")

    results.append({
        'Model': model_label,
        'Eval_Method': 'Rolling-Origin (4 windows)',
        'N_Test_Obs': len(y_trues),
        'MAE_tonnes': round(mae, 0),
        'RMSE_tonnes': round(rmse, 0),
        'MAPE_pct': round(mape, 1),
        'sMAPE_pct': round(smape, 1),
    })

# ARIMA separately (different API)
print(f"\n--- ARIMA(1,1,0) ---")
y_trues_arima = []
y_preds_arima = []
for k in range(min_train, n):
    y_tr = y_all[:k]
    y_te = y_all[k]
    try:
        arima = ARIMA(y_tr, order=(1, 1, 0))
        fitted = arima.fit()
        pred = fitted.forecast(steps=1)[0]
    except Exception as e:
        print(f"  Origin {k}: ARIMA failed — {e}")
        pred = y_tr[-1]  # fallback to naive

    y_trues_arima.append(y_te)
    y_preds_arima.append(pred)
    print(f"  Origin {k}: Train n={k}, Predict FY {df.iloc[k]['financial_year']}: "
          f"Actual={y_te:,.0f}  Predicted={pred:,.0f}  Error={abs(y_te-pred):,.0f}")

    all_predictions.append({
        'model': 'ARIMA(1,1,0)',
        'eval_method': 'rolling_origin',
        'train_size': k,
        'test_fy': df.iloc[k]['financial_year'],
        'actual': y_te,
        'predicted': pred,
        'error': y_te - pred,
        'abs_error': abs(y_te - pred)
    })

mae_a = mean_absolute_error(y_trues_arima, y_preds_arima)
rmse_a = root_mean_squared_error(y_trues_arima, y_preds_arima)
mape_a = calc_mape(y_trues_arima, y_preds_arima)
smape_a = calc_smape(y_trues_arima, y_preds_arima)

print(f"  MAE:  {mae_a:,.0f} tonnes")
print(f"  RMSE: {rmse_a:,.0f} tonnes")
print(f"  MAPE: {mape_a:.1f}%")
print(f"  sMAPE: {smape_a:.1f}%")

results.append({
    'Model': 'ARIMA(1,1,0)',
    'Eval_Method': 'Rolling-Origin (4 windows)',
    'N_Test_Obs': len(y_trues_arima),
    'MAE_tonnes': round(mae_a, 0),
    'RMSE_tonnes': round(rmse_a, 0),
    'MAPE_pct': round(mape_a, 1),
    'sMAPE_pct': round(smape_a, 1),
})

# ============================================================================
# RESULTS TABLE
# ============================================================================
print("\n" + "=" * 80)
print("MODEL COMPARISON TABLE")
print("=" * 80)

df_results = pd.DataFrame(results)
df_results = df_results.sort_values('MAE_tonnes')
print(df_results.to_string(index=False))

df_results.to_csv(os.path.join(PBI_DIR, 'model_metrics.csv'), index=False)
df_results.to_csv(os.path.join(RESULTS_DIR, 'model_metrics.csv'), index=False)
print(f"\nSaved: model_metrics.csv")

df_preds = pd.DataFrame(all_predictions)
df_preds.to_csv(os.path.join(PBI_DIR, 'model_predictions.csv'), index=False)
df_preds.to_csv(os.path.join(RESULTS_DIR, 'model_predictions.csv'), index=False)
print(f"Saved: model_predictions.csv")

print("\n  INTERPRETATION:")
print("  - Lower MAE/RMSE = better prediction accuracy (in tonnes)")
print("  - Lower MAPE/sMAPE = better percentage accuracy")
print("  - With only 4 test windows, rankings are UNSTABLE")
print("  - Models that handle the methodology break better will rank higher")
print("  - Tree-based models (RF, XGBoost) cannot extrapolate beyond training range")

# ============================================================================
# PHASE 5: ROBUSTNESS EXPERIMENTS
# ============================================================================
print("\n" + "=" * 80)
print("PHASE 5: ROBUSTNESS EXPERIMENTS")
print("=" * 80)

robustness_results = []

# --- Experiment A: Limited Training Data ---
print("\n--- Experiment A: Limited Training Data ---")
print("Comparing Linear Regression performance with different training windows")

for train_sizes_label, train_end in [('Full (n=6)', 6), ('Short (n=5)', 5), ('Minimal (n=4)', 4)]:
    X_tr = X_all[:train_end].flatten()
    y_tr = y_all[:train_end]

    # Test on remaining observations
    X_te = X_all[train_end:].flatten()
    y_te = y_all[train_end:]

    if len(y_te) == 0:
        continue

    lr = LinearRegression()
    lr.fit(X_tr.reshape(-1, 1), y_tr)
    preds = lr.predict(X_te.reshape(-1, 1))

    mae = mean_absolute_error(y_te, preds)
    rmse = root_mean_squared_error(y_te, preds)
    mape = calc_mape(y_te, preds)

    print(f"  {train_sizes_label}: MAE={mae:,.0f} T, RMSE={rmse:,.0f} T, MAPE={mape:.1f}%  (test n={len(y_te)})")
    robustness_results.append({
        'experiment': 'A_limited_training',
        'model': 'Linear Regression',
        'config': train_sizes_label,
        'train_n': train_end,
        'test_n': len(y_te),
        'MAE_tonnes': round(mae, 0),
        'RMSE_tonnes': round(rmse, 0),
        'MAPE_pct': round(mape, 1),
    })

# --- Experiment B: Missing Observations ---
print("\n--- Experiment B: Missing Observations (Drop-One) ---")
print("Removing one training observation at a time, training on remainder")

for drop_idx in range(0, 6):
    # Train on all except observation drop_idx (from first 6), test on last 2
    mask = np.ones(6, dtype=bool)
    mask[drop_idx] = False

    X_tr = X_all[:6][mask].flatten()
    y_tr = y_all[:6][mask]
    X_te = X_all[6:].flatten()
    y_te = y_all[6:]
    fw_te = fw_flag[6:]

    lr = LinearRegression()
    lr.fit(X_tr.reshape(-1, 1), y_tr)
    preds = lr.predict(X_te.reshape(-1, 1))

    mae = mean_absolute_error(y_te, preds)
    dropped_fy = df.iloc[drop_idx]['financial_year']
    print(f"  Dropped {dropped_fy}: MAE={mae:,.0f} T, MAPE={calc_mape(y_te, preds):.1f}%")

    robustness_results.append({
        'experiment': 'B_missing_obs',
        'model': 'Linear Regression',
        'config': f'Drop {dropped_fy}',
        'train_n': len(y_tr),
        'test_n': len(y_te),
        'MAE_tonnes': round(mae, 0),
        'RMSE_tonnes': round(root_mean_squared_error(y_te, preds), 0),
        'MAPE_pct': round(calc_mape(y_te, preds), 1),
    })

# --- Experiment C: Noisy Observations ---
print("\n--- Experiment C: Noise Sensitivity (5%, 10%, 20% perturbation) ---")
print("Adding Gaussian noise to training data, testing on clean holdout")

for noise_pct in [5, 10, 20]:
    maes = []
    for trial in range(20):  # 20 random trials
        np.random.seed(42 + trial)
        noise = np.random.normal(0, noise_pct / 100, size=6) * y_all[:6]
        y_noisy = y_all[:6] + noise

        lr = LinearRegression()
        lr.fit(X_all[:6].reshape(-1, 1), y_noisy)
        preds = lr.predict(X_all[6:].reshape(-1, 1))

        mae = mean_absolute_error(y_all[6:], preds)
        maes.append(mae)

    mean_mae = np.mean(maes)
    std_mae = np.std(maes)
    print(f"  Noise {noise_pct}%: Mean MAE={mean_mae:,.0f} ± {std_mae:,.0f} T  (20 trials, seed=42+i)")

    robustness_results.append({
        'experiment': 'C_noise',
        'model': 'Linear Regression',
        'config': f'{noise_pct}% Gaussian noise',
        'train_n': 6,
        'test_n': 2,
        'MAE_tonnes': round(mean_mae, 0),
        'RMSE_tonnes': round(std_mae, 0),  # Using this field for std
        'MAPE_pct': round(calc_mape(y_all[6:], lr.predict(X_all[6:].reshape(-1, 1))), 1),
    })

# --- Experiment D: Forecast Uncertainty (GP) ---
print("\n--- Experiment D: Forecast Uncertainty (Gaussian Process) ---")
gp = GaussianProcessModel()
gp.fit(X_all.flatten(), y_all)
future_X = np.arange(9, 15).reshape(-1, 1)
gp_mean, gp_std = gp.predict(future_X.flatten(), return_std=True)

future_fys = ['2025-26', '2026-27', '2027-28', '2028-29', '2029-30', '2030-31']
print(f"  {'FY':<10} {'Mean (T)':>15} {'Std (T)':>12} {'95% CI Low':>15} {'95% CI High':>15}")
for i, fy in enumerate(future_fys):
    lo = gp_mean[i] - 1.96 * gp_std[i]
    hi = gp_mean[i] + 1.96 * gp_std[i]
    print(f"  {fy:<10} {gp_mean[i]:>15,.0f} {gp_std[i]:>12,.0f} {lo:>15,.0f} {hi:>15,.0f}")

    robustness_results.append({
        'experiment': 'D_uncertainty',
        'model': 'Gaussian Process',
        'config': f'FY {fy}',
        'train_n': 8,
        'test_n': 0,
        'MAE_tonnes': round(gp_mean[i], 0),
        'RMSE_tonnes': round(gp_std[i], 0),
        'MAPE_pct': None,
    })

df_robust = pd.DataFrame(robustness_results)
df_robust.to_csv(os.path.join(PBI_DIR, 'model_robustness_results.csv'), index=False)
df_robust.to_csv(os.path.join(RESULTS_DIR, 'model_robustness_results.csv'), index=False)
print(f"\nSaved: model_robustness_results.csv")

# ============================================================================
# PHASE 6: FUTURE FORECASTS
# ============================================================================
print("\n" + "=" * 80)
print("PHASE 6: FUTURE FORECASTS (2025-26 to 2030-31)")
print("=" * 80)

# Train all models on full data (n=8)
forecast_records = []
future_indices = np.arange(9, 15)  # year_index 9-14

# 1. Naive
naive = NaiveModel()
naive.fit(X_all.flatten(), y_all)
naive_preds = naive.predict(future_indices)

# 2. Linear Regression (no FW flag for future — assume 2022 Rules continues)
lr_full = LinearRegression()
lr_full.fit(X_all, y_all)
lr_preds = lr_full.predict(future_indices.reshape(-1, 1))

# 3. Linear Regression with Framework Flag
lr_fw = LinearRegression()
lr_fw.fit(X_all_with_fw, y_all)
future_fw = np.ones(len(future_indices))  # Future is 2022 Rules
lr_fw_preds = lr_fw.predict(np.column_stack([future_indices, future_fw]))

# 4. ARIMA
arima_full = ARIMA(y_all, order=(1, 1, 0))
arima_fitted = arima_full.fit()
arima_preds = arima_fitted.forecast(steps=6)

# 5. Random Forest
rf = RandomForestModel(use_framework_flag=True)
rf.fit(X_all.flatten(), y_all, fw=fw_flag)
rf_preds = rf.predict(future_indices, fw=future_fw)

# 6. XGBoost
xgb_m = XGBoostModel(use_framework_flag=True)
xgb_m.fit(X_all.flatten(), y_all, fw=fw_flag)
xgb_preds = xgb_m.predict(future_indices, fw=future_fw)

# 7. Gaussian Process (already fitted above)
gp_preds = gp_mean

print(f"\n{'FY':<10} {'Naive':>12} {'LinReg':>12} {'LinReg(FW)':>12} {'ARIMA':>12} "
      f"{'RF':>12} {'XGBoost':>12} {'GP':>12}")
print("-" * 110)
for i, fy in enumerate(future_fys):
    print(f"{fy:<10} {naive_preds[i]:>12,.0f} {lr_preds[i]:>12,.0f} {lr_fw_preds[i]:>12,.0f} "
          f"{arima_preds[i]:>12,.0f} {rf_preds[i]:>12,.0f} {xgb_preds[i]:>12,.0f} "
          f"{gp_preds[i]:>12,.0f}")

    for model_name, pred_val in [
        ('Naive Baseline', naive_preds[i]),
        ('Linear Regression', lr_preds[i]),
        ('Linear Regression (FW)', lr_fw_preds[i]),
        ('ARIMA(1,1,0)', arima_preds[i]),
        ('Random Forest', rf_preds[i]),
        ('XGBoost', xgb_preds[i]),
        ('Gaussian Process', gp_preds[i]),
    ]:
        forecast_records.append({
            'financial_year': fy,
            'fy_start': 2025 + i,
            'model': model_name,
            'forecast_tonnes': round(pred_val, 2),
            'forecast_kt': round(pred_val / 1000, 3),
            'is_forecast': True,
            'forecast_horizon_years': i + 1,
            'gp_std': round(gp_std[i], 2) if model_name == 'Gaussian Process' else None,
            'gp_95ci_low': round(gp_preds[i] - 1.96*gp_std[i], 2) if model_name == 'Gaussian Process' else None,
            'gp_95ci_high': round(gp_preds[i] + 1.96*gp_std[i], 2) if model_name == 'Gaussian Process' else None,
        })

# Add historical actuals for Power BI
for i, row in df.iterrows():
    forecast_records.append({
        'financial_year': row['financial_year'],
        'fy_start': row['fy_start'],
        'model': 'Actual (Historical)',
        'forecast_tonnes': row['ewaste_generated_tonnes'],
        'forecast_kt': row['ewaste_generated_kt'],
        'is_forecast': False,
        'forecast_horizon_years': 0,
        'gp_std': None,
        'gp_95ci_low': None,
        'gp_95ci_high': None,
    })

df_forecasts = pd.DataFrame(forecast_records)
df_forecasts.to_csv(os.path.join(PBI_DIR, 'forecast_results.csv'), index=False)
df_forecasts.to_csv(os.path.join(RESULTS_DIR, 'forecast_results.csv'), index=False)
print(f"\nSaved: forecast_results.csv")

print("\n  IMPORTANT CAVEATS:")
print("  1. All forecasts are based on only 8 historical observations")
print("  2. Methodology break between 2016 Rules and 2022 Rules affects continuity")
print("  3. Tree-based models (RF, XGBoost) CANNOT extrapolate — predictions plateau")
print("  4. GP uncertainty grows rapidly beyond training range")
print("  5. These are MODEL-GENERATED projections, NOT official government forecasts")
print("  6. Long-horizon forecasts (2029-30, 2030-31) should be treated with extreme caution")

# ============================================================================
# PHASE 7: GENERATE VISUALIZATIONS
# ============================================================================
print("\n" + "=" * 80)
print("GENERATING VISUALIZATIONS")
print("=" * 80)

# Figure 1: Historical Trend
fig, ax = plt.subplots(figsize=(10, 6))
colors_fw = ['#2196F3' if g == 'CPCB_2016' else '#FF5722' for g in df['comparability_group']]
ax.bar(df['financial_year'], df['ewaste_generated_tonnes'] / 1e6, color=colors_fw, edgecolor='black', linewidth=0.5)
ax.set_xlabel('Financial Year', fontsize=12)
ax.set_ylabel('E-Waste Generated (Million Tonnes)', fontsize=12)
ax.set_title('India: National E-Waste Generation\n(Source: CPCB/PIB Official Figures)', fontsize=13)
ax.tick_params(axis='x', rotation=45)

# Legend
from matplotlib.patches import Patch
legend_elements = [Patch(facecolor='#2196F3', label='2016 Rules Framework'),
                   Patch(facecolor='#FF5722', label='2022 Rules Framework')]
ax.legend(handles=legend_elements, loc='upper left')
ax.grid(axis='y', alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(FIGURES_DIR, 'fig1_historical_trend.png'), dpi=150)
plt.close()
print("  Saved: fig1_historical_trend.png")

# Figure 2: Forecast Comparison
fig, ax = plt.subplots(figsize=(12, 7))
# Historical
ax.plot(df['fy_start'], df['ewaste_generated_tonnes'] / 1e6, 'ko-', label='Actual', markersize=8, linewidth=2)

model_styles = {
    'Linear Regression': ('b--', 's', 'blue'),
    'Linear Regression (FW)': ('c-.', 'D', 'cyan'),
    'ARIMA(1,1,0)': ('g--', '^', 'green'),
    'Gaussian Process': ('r--', 'v', 'red'),
    'Naive Baseline': ('gray', 'x', 'gray'),
}

for model_name, (ls, mk, clr) in model_styles.items():
    mask = (df_forecasts['model'] == model_name) & (df_forecasts['is_forecast'] == True)
    subset = df_forecasts[mask].sort_values('fy_start')
    if len(subset) > 0:
        ax.plot(subset['fy_start'], subset['forecast_tonnes'] / 1e6,
                ls, marker=mk, color=clr, label=model_name, markersize=5, alpha=0.8)

# GP uncertainty band
gp_mask = (df_forecasts['model'] == 'Gaussian Process') & (df_forecasts['is_forecast'] == True)
gp_sub = df_forecasts[gp_mask].sort_values('fy_start')
if len(gp_sub) > 0:
    ax.fill_between(gp_sub['fy_start'],
                    gp_sub['gp_95ci_low'] / 1e6,
                    gp_sub['gp_95ci_high'] / 1e6,
                    alpha=0.15, color='red', label='GP 95% CI')

ax.axvline(x=2022.5, color='orange', linestyle=':', alpha=0.5, label='Methodology break')
ax.set_xlabel('Financial Year Start', fontsize=12)
ax.set_ylabel('E-Waste Generated (Million Tonnes)', fontsize=12)
ax.set_title('Forecast Comparison: E-Waste Generation in India\n'
             '(Comparative Analysis of Predictive Models)', fontsize=13)
ax.legend(fontsize=9, loc='upper left')
ax.grid(alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(FIGURES_DIR, 'fig2_forecast_comparison.png'), dpi=150)
plt.close()
print("  Saved: fig2_forecast_comparison.png")

# Figure 3: Model Performance Comparison
fig, axes = plt.subplots(1, 3, figsize=(15, 5))
df_res_sorted = df_results.sort_values('MAE_tonnes')

axes[0].barh(df_res_sorted['Model'], df_res_sorted['MAE_tonnes'] / 1000, color='steelblue')
axes[0].set_xlabel('MAE (thousand tonnes)')
axes[0].set_title('Mean Absolute Error')

axes[1].barh(df_res_sorted['Model'], df_res_sorted['RMSE_tonnes'] / 1000, color='coral')
axes[1].set_xlabel('RMSE (thousand tonnes)')
axes[1].set_title('Root Mean Squared Error')

axes[2].barh(df_res_sorted['Model'], df_res_sorted['MAPE_pct'], color='seagreen')
axes[2].set_xlabel('MAPE (%)')
axes[2].set_title('Mean Absolute % Error')

plt.suptitle('Model Performance Comparison (Rolling-Origin, 4 Windows)', fontsize=13, y=1.02)
plt.tight_layout()
plt.savefig(os.path.join(FIGURES_DIR, 'fig3_model_performance.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  Saved: fig3_model_performance.png")

# Figure 4: Robustness — Noise Sensitivity
noise_data = df_robust[df_robust['experiment'] == 'C_noise']
if len(noise_data) > 0:
    fig, ax = plt.subplots(figsize=(8, 5))
    configs = noise_data['config'].values
    maes = noise_data['MAE_tonnes'].values
    stds = noise_data['RMSE_tonnes'].values
    ax.bar(configs, maes / 1000, yerr=stds / 1000, capsize=5, color='sandybrown', edgecolor='black')
    ax.set_xlabel('Noise Level')
    ax.set_ylabel('MAE (thousand tonnes)')
    ax.set_title('Robustness: Impact of Training Data Noise\n(Linear Regression, 20 trials per level)')
    ax.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(FIGURES_DIR, 'fig4_noise_robustness.png'), dpi=150)
    plt.close()
    print("  Saved: fig4_noise_robustness.png")

# Figure 5: GP Uncertainty Growth
fig, ax = plt.subplots(figsize=(10, 6))
# Historical
ax.plot(df['fy_start'], df['ewaste_generated_tonnes'] / 1e6, 'ko-', label='Actual', markersize=8, linewidth=2)
# GP forecast
gp_years = [2025 + i for i in range(6)]
ax.plot(gp_years, gp_mean / 1e6, 'r-o', label='GP Mean Forecast', markersize=6)
ax.fill_between(gp_years, (gp_mean - 1.96*gp_std) / 1e6, (gp_mean + 1.96*gp_std) / 1e6,
                alpha=0.2, color='red', label='95% Prediction Interval')
ax.fill_between(gp_years, (gp_mean - gp_std) / 1e6, (gp_mean + gp_std) / 1e6,
                alpha=0.3, color='red', label='68% Prediction Interval')
ax.axvline(x=2022.5, color='orange', linestyle=':', alpha=0.5, label='Methodology break')
ax.set_xlabel('Year')
ax.set_ylabel('E-Waste Generated (Million Tonnes)')
ax.set_title('Gaussian Process: Forecast with Uncertainty Bands')
ax.legend()
ax.grid(alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(FIGURES_DIR, 'fig5_gp_uncertainty.png'), dpi=150)
plt.close()
print("  Saved: fig5_gp_uncertainty.png")

# Figure 6: Limited Training Data
ltd_data = df_robust[df_robust['experiment'] == 'A_limited_training']
if len(ltd_data) > 0:
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(ltd_data['config'], ltd_data['MAE_tonnes'] / 1000, color='mediumpurple', edgecolor='black')
    ax.set_xlabel('Training Data Size')
    ax.set_ylabel('MAE (thousand tonnes)')
    ax.set_title('Robustness: Impact of Training Data Size\n(Linear Regression)')
    ax.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(FIGURES_DIR, 'fig6_training_size.png'), dpi=150)
    plt.close()
    print("  Saved: fig6_training_size.png")

print("\n" + "=" * 80)
print("ALL PHASES COMPLETE")
print("=" * 80)
print(f"\nOutput files in: {PBI_DIR}")
print(f"Figures in: {FIGURES_DIR}")

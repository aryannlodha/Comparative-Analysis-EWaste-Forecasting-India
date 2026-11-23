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
from statsmodels.tools.sm_exceptions import ConvergenceWarning
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
    """Gaussian Process Regression with RBF kernel, fitted in standardized log space.

    Modelling log(tonnes) keeps every prediction (and interval bound) strictly
    positive, and standardizing the target lets the kernel hyperparameters live on
    an O(1) scale instead of the old 1e12 / 1e8 magnitudes needed for raw tonnes.
    The returned point forecast is the median (exp of the log-space mean), and
    intervals are exp(log-mean +/- z * log-std).
    """
    def __init__(self, use_framework_flag=False):
        kernel = ConstantKernel(1.0, (1e-2, 1e2)) * RBF(2.0, (0.5, 10.0)) + WhiteKernel(0.1, (1e-4, 1.0))
        self.model = GaussianProcessRegressor(
            kernel=kernel, n_restarts_optimizer=10, random_state=42, alpha=0
        )
        self.use_fw = use_framework_flag
        self.name = "Gaussian Process"
        self._mu = 0.0
        self._sd = 1.0

    def fit(self, X, y, fw=None):
        if self.use_fw and fw is not None:
            X_train = np.column_stack([X, fw])
        else:
            X_train = X.reshape(-1, 1) if X.ndim == 1 else X
        log_y = np.log(np.asarray(y, dtype=float))
        self._mu = log_y.mean()
        self._sd = log_y.std() or 1.0
        self.model.fit(X_train, (log_y - self._mu) / self._sd)

    def _design(self, X, fw=None):
        if self.use_fw and fw is not None:
            return np.column_stack([X, fw])
        return X.reshape(-1, 1) if X.ndim == 1 else X

    def predict(self, X, fw=None, return_std=False):
        """Median forecast in tonnes. With return_std=True also returns the
        log-space standard deviation (a unitless multiplicative-uncertainty scale)."""
        z_mean, z_std = self.model.predict(self._design(X, fw), return_std=True)
        median = np.exp(z_mean * self._sd + self._mu)
        if return_std:
            return median, z_std * self._sd
        return median

    def predict_interval(self, X, fw=None, z=1.96):
        """(median, low, high) in tonnes; bounds are always > 0."""
        median, log_std = self.predict(X, fw=fw, return_std=True)
        return median, median * np.exp(-z * log_std), median * np.exp(z * log_std)

    def description(self):
        return {
            'name': self.name,
            'how_it_works': 'Bayesian nonparametric regression with RBF kernel on standardized '
                           'log(tonnes); median forecast plus multiplicative (log-normal) intervals',
            'why_included': 'Naturally provides prediction uncertainty estimates',
            'assumptions': 'Smooth underlying function of log-tonnes; Gaussian noise in log space',
            'limitations': 'Small dataset means wide uncertainty bands; '
                          'kernel hyperparameters may be poorly identified',
            'input_variables': 'year_index' + (', framework_flag' if self.use_fw else ''),
            'training_method': 'Marginal likelihood optimization (seed=42)',
            'validation_method': 'Chronological holdout'
        }


ARIMA_DIAGNOSTICS = []  # every fallback / convergence problem is recorded here and saved


def arima_forecast(y_train, steps, order=(1, 1, 0), trend='n', context=''):
    """Fit ARIMA and forecast `steps` ahead.

    Failures are never silent: if the fit raises or returns a non-finite forecast we
    fall back to the naive last value, print a loud WARNING, and record the event in
    ARIMA_DIAGNOSTICS (saved to outputs/model_results/arima_diagnostics.csv).
    Convergence warnings are recorded too, even though the forecast is still used.
    `trend='t'` adds a drift term (meaningful for d=1).
    """
    y_train = np.asarray(y_train, dtype=float)
    event = {'context': context, 'order': str(order), 'trend': trend}
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        try:
            fc = np.asarray(ARIMA(y_train, order=order, trend=trend).fit().forecast(steps=steps), dtype=float)
            if not np.all(np.isfinite(fc)):
                raise ValueError('non-finite forecast')
        except Exception as e:
            fc = np.full(steps, y_train[-1])
            ARIMA_DIAGNOSTICS.append({**event, 'event': 'FALLBACK_TO_NAIVE', 'detail': str(e)[:200]})
            print(f"  !!! WARNING: ARIMA{order} trend='{trend}' [{context}] FAILED ({e}); using naive fallback")
    for w in caught:
        if issubclass(w.category, ConvergenceWarning):
            ARIMA_DIAGNOSTICS.append({**event, 'event': 'CONVERGENCE_WARNING', 'detail': str(w.message)[:200]})
            print(f"  !!! WARNING: ARIMA{order} trend='{trend}' [{context}] convergence warning")
    return fc


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
    pred = arima_forecast(y_tr, 1, order=(1, 1, 0), context=f'rolling_origin_k{k}')[0]

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
print("  - With only 4 test windows, rankings are UNSTABLE (see fold_sensitivity.csv)")
print("  - The methodology break falls inside the backtest (fold 3 targets FY 2023-24)")
print("  - Tree-based models (RF, XGBoost) cannot extrapolate beyond training range")

# ----------------------------------------------------------------------------
# DIAGNOSTIC 1: is the framework flag actually informative in each fold?
# ----------------------------------------------------------------------------
print("\n--- Diagnostic: framework-flag identifiability per fold ---")
fw_diag = []
for k in range(min_train, n):
    fw_tr = fw_flag[:k]
    n_post = int((fw_tr == 1).sum())
    coef = np.nan
    if n_post > 0 and n_post < k:
        m_fw = LinearRegression().fit(np.column_stack([X_all[:k].flatten(), fw_tr]), y_all[:k])
        coef = m_fw.coef_[1]
    identified = 0 < n_post < k
    fw_diag.append({
        'train_size': k,
        'test_fy': df.iloc[k]['financial_year'],
        'post_break_points_in_train': n_post,
        'flag_identified': identified,
        'flag_coefficient_tonnes': round(coef, 0) if identified else None,
    })
    status = (f"coef={coef:,.0f} T (estimated from {n_post} post-break point(s))" if identified
              else "flag is CONSTANT in training data -> not identified; FW model == standard LR")
    print(f"  Fold k={k} (predict {df.iloc[k]['financial_year']}): {status}")
n_identified = sum(r['flag_identified'] for r in fw_diag)
print(f"  => The flag is identified in only {n_identified} of {len(fw_diag)} folds, so any FW-vs-standard "
      f"difference comes from those folds alone.")
pd.DataFrame(fw_diag).to_csv(os.path.join(RESULTS_DIR, 'framework_flag_diagnostic.csv'), index=False)
pd.DataFrame(fw_diag).to_csv(os.path.join(PBI_DIR, 'framework_flag_diagnostic.csv'), index=False)

# ----------------------------------------------------------------------------
# DIAGNOSTIC 2: how fragile is the ranking? Per-fold errors and drop-one-fold MAE
# ----------------------------------------------------------------------------
print("\n--- Diagnostic: ranking stability (MAE with each fold dropped) ---")
sens_rows = []
fold_ks = list(range(min_train, n))
for model_label, g in df_preds.groupby('model'):
    errs = g.sort_values('train_size')['abs_error'].values
    row = {'model': model_label, 'MAE_all_folds': round(errs.mean(), 0)}
    for j, k in enumerate(fold_ks):
        row[f'MAE_without_fold_{df.iloc[k]["financial_year"]}'] = round(np.delete(errs, j).mean(), 0)
        row[f'abs_err_{df.iloc[k]["financial_year"]}'] = round(errs[j], 0)
    sens_rows.append(row)
df_sens = pd.DataFrame(sens_rows).sort_values('MAE_all_folds')
drop_cols = [c for c in df_sens.columns if c.startswith('MAE_without_fold_')]
ranks = df_sens.set_index('model')[['MAE_all_folds'] + drop_cols].rank()
df_sens['best_rank'] = df_sens['model'].map(ranks.min(axis=1)).astype(int)
df_sens['worst_rank'] = df_sens['model'].map(ranks.max(axis=1)).astype(int)
df_sens.to_csv(os.path.join(RESULTS_DIR, 'fold_sensitivity.csv'), index=False)
df_sens.to_csv(os.path.join(PBI_DIR, 'fold_sensitivity.csv'), index=False)
print(df_sens[['model', 'MAE_all_folds', 'best_rank', 'worst_rank']].to_string(index=False))
print("  => A wide best_rank..worst_rank span means the ranking is NOT statistically meaningful.")

# ----------------------------------------------------------------------------
# DIAGNOSTIC 3: ARIMA order / drift comparison (same rolling-origin folds)
# ----------------------------------------------------------------------------
print("\n--- Diagnostic: ARIMA order and drift comparison ---")
arima_rows = []
for order in [(0, 1, 0), (1, 1, 0), (0, 1, 1), (1, 1, 1)]:
    for trend in ['n', 't']:
        preds_o = [arima_forecast(y_all[:k], 1, order=order, trend=trend, context=f'order_search_k{k}')[0]
                   for k in range(min_train, n)]
        mae_o = mean_absolute_error(y_all[min_train:], preds_o)
        arima_rows.append({'order': str(order), 'drift': trend == 't', 'MAE_tonnes': round(mae_o, 0),
                           'MAPE_pct': round(calc_mape(y_all[min_train:], preds_o), 1)})
        print(f"  ARIMA{order} drift={trend == 't'}: MAE={mae_o:,.0f} T")
df_arima_cmp = pd.DataFrame(arima_rows).sort_values('MAE_tonnes')
df_arima_cmp.to_csv(os.path.join(RESULTS_DIR, 'arima_order_comparison.csv'), index=False)
df_arima_cmp.to_csv(os.path.join(PBI_DIR, 'arima_order_comparison.csv'), index=False)
print("  Headline model stays ARIMA(1,1,0) (no drift) for continuity; this table is a sensitivity check.")

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

# The final two financial years form a common holdout for experiments A–C.
X_history, X_te = X_all[:-2], X_all[-2:]
y_history, y_te = y_all[:-2], y_all[-2:]
for train_sizes_label, train_n in [('Full (n=6)', 6), ('Short (n=5)', 5), ('Minimal (n=4)', 4)]:
    X_tr = X_history[-train_n:]
    y_tr = y_history[-train_n:]

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
        'train_n': train_n,
        'test_n': len(y_te),
        'MAE_tonnes': round(mae, 0),
        'RMSE_tonnes': round(rmse, 0),
        'MAPE_pct': round(mape, 1),
    })

# --- Experiment B: Missing Observations ---
print("\n--- Experiment B: Missing Observations (Drop-One) ---")
print("Removing one training observation at a time, training on remainder")

for drop_idx in range(len(y_history)):
    mask = np.ones(len(y_history), dtype=bool)
    mask[drop_idx] = False

    X_tr = X_history[mask]
    y_tr = y_history[mask]

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
    mapes = []
    for trial in range(20):  # 20 random trials
        rng = np.random.RandomState(42 + trial)
        noise = rng.normal(0, noise_pct / 100, size=len(y_history)) * y_history
        y_noisy = y_history + noise

        lr = LinearRegression()
        lr.fit(X_history, y_noisy)
        preds = lr.predict(X_te)

        maes.append(mean_absolute_error(y_te, preds))
        mapes.append(calc_mape(y_te, preds))

    mean_mae = np.mean(maes)
    std_mae = np.std(maes)
    print(f"  Noise {noise_pct}%: Mean MAE={mean_mae:,.0f} ± {std_mae:,.0f} T  (20 trials, seed=42+i)")

    robustness_results.append({
        'experiment': 'C_noise',
        'model': 'Linear Regression',
        'config': f'{noise_pct}% Gaussian noise',
        'train_n': len(y_history),
        'test_n': len(y_te),
        'trial_count': len(maes),
        'mean_MAE_tonnes': round(mean_mae, 0),
        'std_MAE_tonnes': round(std_mae, 0),
        'mean_MAPE_pct': round(np.mean(mapes), 1),
    })

# --- Experiment D: Forecast Uncertainty (GP) ---
print("\n--- Experiment D: Forecast Uncertainty (Gaussian Process) ---")
gp = GaussianProcessModel()
gp.fit(X_all.flatten(), y_all)
future_X = np.arange(9, 15).reshape(-1, 1)
# The GP works in log space: gp_mean is the median forecast and every interval bound is > 0.
gp_mean, gp_lo, gp_hi = gp.predict_interval(future_X.flatten(), z=1.96)
_, gp_lo68, gp_hi68 = gp.predict_interval(future_X.flatten(), z=1.0)
# "Equivalent std" in tonnes: half-width of the 95% interval / 1.96 (intervals are asymmetric).
gp_std = (gp_hi - gp_lo) / (2 * 1.96)

future_fys = ['2025-26', '2026-27', '2027-28', '2028-29', '2029-30', '2030-31']
print(f"  {'FY':<10} {'Median (T)':>15} {'Equiv Std (T)':>14} {'95% CI Low':>15} {'95% CI High':>15}")
for i, fy in enumerate(future_fys):
    lo, hi = gp_lo[i], gp_hi[i]
    print(f"  {fy:<10} {gp_mean[i]:>15,.0f} {gp_std[i]:>14,.0f} {lo:>15,.0f} {hi:>15,.0f}")

    robustness_results.append({
        'experiment': 'D_uncertainty',
        'model': 'Gaussian Process',
        'config': f'FY {fy}',
        'train_n': 8,
        'test_n': 0,
        'forecast_mean_tonnes': round(gp_mean[i], 0),
        'forecast_std_tonnes': round(gp_std[i], 0),
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
arima_preds = arima_forecast(y_all, 6, order=(1, 1, 0), context='final_6_step_forecast')

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
            'gp_95ci_low': round(gp_lo[i], 2) if model_name == 'Gaussian Process' else None,
            'gp_95ci_high': round(gp_hi[i], 2) if model_name == 'Gaussian Process' else None,
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

# ----------------------------------------------------------------------------
# SCENARIO BAND: one range instead of seven competing point forecasts
# ----------------------------------------------------------------------------
# RF and XGBoost are excluded: trees cannot extrapolate, so their forecast is just a
# plateau of the recent level and adds no information about trend uncertainty.
band_models = {
    'Naive Baseline': naive_preds,
    'Linear Regression': lr_preds,
    'Linear Regression (FW)': lr_fw_preds,
    'ARIMA(1,1,0)': np.asarray(arima_preds),
    'Gaussian Process': gp_preds,
}
band_matrix = np.vstack(list(band_models.values()))
band_names = list(band_models.keys())
band_records = []
for i, fy in enumerate(future_fys):
    col = band_matrix[:, i]
    band_records.append({
        'financial_year': fy,
        'fy_start': 2025 + i,
        'low_tonnes': round(col.min(), 0),
        'base_tonnes': round(float(np.median(col)), 0),
        'high_tonnes': round(col.max(), 0),
        'low_defined_by': band_names[int(col.argmin())],
        'high_defined_by': band_names[int(col.argmax())],
        'models_in_band': '; '.join(band_names),
        'excluded_models': 'Random Forest; XGBoost (cannot extrapolate)',
    })
df_band = pd.DataFrame(band_records)
df_band.to_csv(os.path.join(PBI_DIR, 'scenario_band.csv'), index=False)
df_band.to_csv(os.path.join(RESULTS_DIR, 'scenario_band.csv'), index=False)
print("\nSCENARIO BAND (min / median / max across Naive, LR, LR-FW, ARIMA, GP):")
print(df_band[['financial_year', 'low_tonnes', 'base_tonnes', 'high_tonnes',
               'low_defined_by', 'high_defined_by']].to_string(index=False))
print("Saved: scenario_band.csv")

# ARIMA problems must never be silent
df_arima_diag = pd.DataFrame(ARIMA_DIAGNOSTICS, columns=['context', 'order', 'trend', 'event', 'detail'])
df_arima_diag.to_csv(os.path.join(RESULTS_DIR, 'arima_diagnostics.csv'), index=False)
if len(df_arima_diag):
    print(f"\n!!! {len(df_arima_diag)} ARIMA fallback/convergence event(s) recorded — see arima_diagnostics.csv")
else:
    print("\nARIMA diagnostics: no fallbacks or convergence warnings (arima_diagnostics.csv is empty).")

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
    maes = noise_data['mean_MAE_tonnes'].values
    stds = noise_data['std_MAE_tonnes'].values
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
ax.fill_between(gp_years, gp_lo / 1e6, gp_hi / 1e6,
                alpha=0.2, color='red', label='95% Prediction Interval (log-normal, always > 0)')
ax.fill_between(gp_years, gp_lo68 / 1e6, gp_hi68 / 1e6,
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
    ax.set_title('Linear Regression by Training Window Size\nCommon holdout: FY 2023–24 and FY 2024–25')
    ax.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(FIGURES_DIR, 'fig6_training_size.png'), dpi=150)
    plt.close()
    print("  Saved: fig6_training_size.png")

# Figure 7: Scenario band (the headline forecast presentation)
fig, ax = plt.subplots(figsize=(10, 6))
ax.plot(df['fy_start'], df['ewaste_generated_tonnes'] / 1e6, 'ko-', label='Actual', markersize=8, linewidth=2)
ax.fill_between(df_band['fy_start'], df_band['low_tonnes'] / 1e6, df_band['high_tonnes'] / 1e6,
                alpha=0.25, color='tab:blue', label='Scenario range (min–max of 5 extrapolating models)')
ax.plot(df_band['fy_start'], df_band['base_tonnes'] / 1e6, 'b-o', label='Median of models', markersize=5)
ax.axvline(x=2022.5, color='orange', linestyle=':', alpha=0.6, label='Methodology break')
ax.set_xlabel('Financial Year Start')
ax.set_ylabel('E-Waste Generated (Million Tonnes)')
ax.set_title('Forecast Scenario Range, FY 2025–26 to 2030–31\n'
             'Based on 8 observations and one reporting-framework break: a range, not a prediction')
ax.legend(loc='upper left', fontsize=9)
ax.grid(alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(FIGURES_DIR, 'fig7_scenario_band.png'), dpi=150)
plt.close()
print("  Saved: fig7_scenario_band.png")

print("\n" + "=" * 80)
print("ALL PHASES COMPLETE")
print("=" * 80)
print(f"\nOutput files in: {PBI_DIR}")
print(f"Figures in: {FIGURES_DIR}")

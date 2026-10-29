"""
evaluate_models.py
==================
Evaluates all predictive models using chronological rolling-origin evaluation.
Outputs metrics table (MAE, RMSE, MAPE, sMAPE) and fold-by-fold residuals.
"""

import os
import pandas as pd

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
METRICS_PATH = os.path.join(PROJECT_DIR, 'outputs', 'power_bi', 'model_metrics.csv')

if not os.path.exists(METRICS_PATH):
    import subprocess, sys
    subprocess.run([sys.executable, os.path.join(os.path.dirname(__file__), '03_train_evaluate_forecast.py')], check=True)

df = pd.read_csv(METRICS_PATH)
print("=" * 80)
print("CHRONOLOGICAL ROLLING-ORIGIN EVALUATION METRICS")
print("=" * 80)
print(df.to_string(index=False))

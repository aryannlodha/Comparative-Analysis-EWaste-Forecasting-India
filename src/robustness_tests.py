"""
robustness_tests.py
===================
Executes and displays Phase 5 model reliability experiments:
  - Experiment A: Training window contraction
  - Experiment B: Missing data (Jackknife leave-one-out)
  - Experiment C: Gaussian noise perturbation (5%, 10%, 20%)
  - Experiment D: Gaussian Process predictive uncertainty expansion
"""

import os
import pandas as pd

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROBUST_PATH = os.path.join(PROJECT_DIR, 'outputs', 'power_bi', 'model_robustness_results.csv')

if not os.path.exists(ROBUST_PATH):
    import subprocess, sys
    subprocess.run([sys.executable, os.path.join(os.path.dirname(__file__), '03_train_evaluate_forecast.py')], check=True)

df = pd.read_csv(ROBUST_PATH)
print("=" * 80)
print("PHASE 5: MODEL ROBUSTNESS & RELIABILITY RESULTS")
print("=" * 80)
for exp_name, group in df.groupby('experiment'):
    print(f"\n--- {exp_name} ---")
    print(group[['config', 'train_n', 'test_n', 'MAE_tonnes', 'RMSE_tonnes', 'MAPE_pct']].to_string(index=False))

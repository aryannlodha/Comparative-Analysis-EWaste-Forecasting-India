"""
train_models.py
===============
Trains the candidate predictive models:
  - Naive Baseline
  - Linear Regression (Standard & Framework Adjusted)
  - ARIMA(1,1,0)
  - Random Forest Regressor
  - XGBoost Regressor
  - Gaussian Process Regressor
"""

import os
import sys

# Runs Phase 3 training routines
script_path = os.path.join(os.path.dirname(__file__), '03_train_evaluate_forecast.py')
import subprocess
result = subprocess.run([sys.executable, script_path], check=True)
sys.exit(result.returncode)

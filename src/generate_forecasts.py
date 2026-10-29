"""
generate_forecasts.py
=====================
Displays and verifies multi-model future forecasts through FY 2030-31.
"""

import os
import pandas as pd

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FC_PATH = os.path.join(PROJECT_DIR, 'outputs', 'power_bi', 'forecast_results.csv')

if not os.path.exists(FC_PATH):
    import subprocess, sys
    subprocess.run([sys.executable, os.path.join(os.path.dirname(__file__), '03_train_evaluate_forecast.py')], check=True)

df = pd.read_csv(FC_PATH)
df_future = df[df['is_forecast'] == True]

print("=" * 80)
print("PHASE 6: MULTI-MODEL FORECASTS (FY 2025-26 TO FY 2030-31)")
print("=" * 80)
piv = df_future.pivot(index='financial_year', columns='model', values='forecast_tonnes')
print(piv.map(lambda x: f"{x:,.0f} MT" if pd.notna(x) else "-"))

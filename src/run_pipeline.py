"""
run_pipeline.py
===============
Executes the complete end-to-end e-waste forecasting pipeline in sequence:
  1. 01_inspect_and_audit.py
  2. 02_prepare_data.py
  3. 03_train_evaluate_forecast.py
  4. generate_interactive_dashboard.py
"""

import os
import sys
import subprocess

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(PROJECT_DIR, 'src')

steps = [
    '01_inspect_and_audit.py',
    '02_prepare_data.py',
    '03_train_evaluate_forecast.py',
    'generate_interactive_dashboard.py'
]

print("=" * 80)
print("EXECUTING END-TO-END EIS PIPELINE")
print("=" * 80)

for step in steps:
    step_path = os.path.join(SRC_DIR, step)
    print(f"\n>>> Running: {step} ...")
    res = subprocess.run([sys.executable, step_path])
    if res.returncode != 0:
        print(f"FAILED: {step} exited with code {res.returncode}")
        sys.exit(res.returncode)

print("\n" + "=" * 80)
print("PIPELINE COMPLETED SUCCESSFULLY!")
print(f"Decision-support dashboard: {os.path.join(PROJECT_DIR, 'outputs', 'dashboard', 'index.html')}")
print("=" * 80)

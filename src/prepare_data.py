"""
prepare_data.py
===============
Executes Phase 2 data preparation pipeline.
Constructs verified national time series, applies derived features,
defines chronological holdout splits, and exports model-ready CSVs.
"""

import subprocess
import sys
import os

script_path = os.path.join(os.path.dirname(__file__), '02_prepare_data.py')
result = subprocess.run([sys.executable, script_path], check=True)
sys.exit(result.returncode)

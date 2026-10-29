"""
audit_data.py
=============
Executes Phase 1 data audit, cross-source reconciliation, and quality checks.
Exports:
  - outputs/power_bi/data_quality_report.csv
  - outputs/power_bi/source_register.csv
  - outputs/reports/cross_source_comparison.csv
"""

import subprocess
import sys
import os

script_path = os.path.join(os.path.dirname(__file__), '01_inspect_and_audit.py')
result = subprocess.run([sys.executable, script_path], check=True)
sys.exit(result.returncode)

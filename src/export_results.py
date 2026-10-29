"""
export_results.py
=================
Verifies and lists all Power BI and tabular artifacts exported by the pipeline.
"""

import os
import glob
import pandas as pd

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PBI_DIR = os.path.join(PROJECT_DIR, 'outputs', 'power_bi')

print("=" * 80)
print("EXPORTED POWER BI CSV MANIFEST")
print("=" * 80)

for fpath in sorted(glob.glob(os.path.join(PBI_DIR, '*.csv'))):
    fname = os.path.basename(fpath)
    df = pd.read_csv(fpath)
    size_kb = os.path.getsize(fpath) / 1024
    print(f"  - {fname:<30} {len(df):>4} rows, {len(df.columns):>2} cols, {size_kb:>6.2f} KB")

print("\nAll files ready for Power BI consumption.")

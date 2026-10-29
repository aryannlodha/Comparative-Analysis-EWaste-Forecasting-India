"""
02_prepare_data.py
==================
Phase 2: Data Preparation Pipeline
Project: Comparative Analysis of Predictive Models for E-Waste Generation Forecasting in India

This script:
  1. Creates the cleaned national e-waste generation dataset
  2. Standardizes years, units, and formats
  3. Documents all transformations
  4. Separates the dataset into training and holdout sets (chronological)
  5. Exports model-ready data
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROCESSED_DIR = os.path.join(PROJECT_DIR, 'data', 'processed')
PBI_DIR = os.path.join(PROJECT_DIR, 'outputs', 'power_bi')
os.makedirs(PROCESSED_DIR, exist_ok=True)
os.makedirs(PBI_DIR, exist_ok=True)

print("=" * 80)
print("PHASE 2: DATA PREPARATION")
print("=" * 80)

# ============================================================================
# 1. CONSTRUCT THE VERIFIED NATIONAL E-WASTE GENERATION DATASET
# ============================================================================
print("\n1. CONSTRUCTING VERIFIED DATASET")
print("-" * 40)

# Each row is a verified observation with full provenance
data = [
    {
        'record_id': 'IN001',
        'financial_year': '2017-18',
        'fy_start': 2017,
        'year_index': 1,  # For regression: ordinal time index
        'ewaste_generated_tonnes': 708445.00,
        'ewaste_generated_kt': 708.445,
        'data_status': 'Official figure',
        'data_type': 'CPCB estimate (producer sales + avg useful life)',
        'reporting_framework': '2016 Rules',
        'comparability_group': 'CPCB_2016',
        'source_id': 'S01',
        'source_url': 'https://www.pib.gov.in/PressReleasePage.aspx?PRID=1943201',
        'notes': 'PIB release 27 Jul 2023. 21 notified EEE types.'
    },
    {
        'record_id': 'IN002',
        'financial_year': '2018-19',
        'fy_start': 2018,
        'year_index': 2,
        'ewaste_generated_tonnes': 771215.00,
        'ewaste_generated_kt': 771.215,
        'data_status': 'Official figure',
        'data_type': 'CPCB estimate (producer sales + avg useful life)',
        'reporting_framework': '2016 Rules',
        'comparability_group': 'CPCB_2016',
        'source_id': 'S01',
        'source_url': 'https://www.pib.gov.in/PressReleasePage.aspx?PRID=1943201',
        'notes': 'PIB release 27 Jul 2023. 21 notified EEE types.'
    },
    {
        'record_id': 'IN003',
        'financial_year': '2019-20',
        'fy_start': 2019,
        'year_index': 3,
        'ewaste_generated_tonnes': 1014961.21,
        'ewaste_generated_kt': 1014.961,
        'data_status': 'Official figure',
        'data_type': 'CPCB estimate (producer sales + avg useful life)',
        'reporting_framework': '2016 Rules',
        'comparability_group': 'CPCB_2016',
        'source_id': 'S01',
        'source_url': 'https://www.pib.gov.in/PressReleasePage.aspx?PRID=1943201',
        'notes': 'PIB release 27 Jul 2023. Also confirmed by RS Session CSV.'
    },
    {
        'record_id': 'IN004',
        'financial_year': '2020-21',
        'fy_start': 2020,
        'year_index': 4,
        'ewaste_generated_tonnes': 1346496.31,
        'ewaste_generated_kt': 1346.496,
        'data_status': 'Official figure',
        'data_type': 'CPCB estimate (producer sales + avg useful life)',
        'reporting_framework': '2016 Rules',
        'comparability_group': 'CPCB_2016',
        'source_id': 'S01',
        'source_url': 'https://www.pib.gov.in/PressReleasePage.aspx?PRID=1943201',
        'notes': 'PIB release 27 Jul 2023. Also confirmed by RS Session CSV.'
    },
    {
        'record_id': 'IN005',
        'financial_year': '2021-22',
        'fy_start': 2021,
        'year_index': 5,
        'ewaste_generated_tonnes': 1601155.36,
        'ewaste_generated_kt': 1601.155,
        'data_status': 'Official figure',
        'data_type': 'CPCB estimate (producer sales + avg useful life)',
        'reporting_framework': '2016 Rules',
        'comparability_group': 'CPCB_2016',
        'source_id': 'S01',
        'source_url': 'https://www.pib.gov.in/PressReleasePage.aspx?PRID=1943201',
        'notes': 'PIB release 27 Jul 2023. Also confirmed by RS Session CSV.'
    },
    {
        'record_id': 'IN006',
        'financial_year': '2022-23',
        'fy_start': 2022,
        'year_index': 6,
        'ewaste_generated_tonnes': 1609117.00,
        'ewaste_generated_kt': 1609.117,
        'data_status': 'Official figure',
        'data_type': 'CPCB estimate',
        'reporting_framework': '2016 Rules',
        'comparability_group': 'CPCB_2016',
        'source_id': 'S_RS + E-WASTE VALUE.xlsx',
        'source_url': 'Parliamentary source + workbook cross-check',
        'notes': 'Value confirmed from RS Session CSV (1,609,117) and E-WASTE VALUE.xlsx. '
                 'Also verified via web search against official parliamentary answer. '
                 'Growth rate slows dramatically (0.5%) compared to prior years (18-33%).'
    },
    {
        'record_id': 'IN007',
        'financial_year': '2023-24',
        'fy_start': 2023,
        'year_index': 7,
        'ewaste_generated_tonnes': 1254286.55,
        'ewaste_generated_kt': 1254.287,
        'data_status': 'Official figure',
        'data_type': 'CPCB estimate (registered-producer sales + avg useful life)',
        'reporting_framework': '2022 Rules',
        'comparability_group': 'CPCB_2022',
        'source_id': 'S02',
        'source_url': 'https://www.pib.gov.in/PressReleasePage.aspx?PRID=2147876',
        'notes': 'PIB release 24 Jul 2025. Different Rules framework from 2016 series. '
                 'RS Session CSV reports 1,751,236 for same FY under different methodology. '
                 'VALUE IS LOWER than 2022-23 under old Rules — methodology break, not decline.'
    },
    {
        'record_id': 'IN008',
        'financial_year': '2024-25',
        'fy_start': 2024,
        'year_index': 8,
        'ewaste_generated_tonnes': 1397955.59,
        'ewaste_generated_kt': 1397.956,
        'data_status': 'Official figure',
        'data_type': 'CPCB estimate (registered-producer sales + avg useful life)',
        'reporting_framework': '2022 Rules',
        'comparability_group': 'CPCB_2022',
        'source_id': 'S02',
        'source_url': 'https://www.pib.gov.in/PressReleasePage.aspx?PRID=2147876',
        'notes': 'PIB release 24 Jul 2025. 2022 Rules framework.'
    },
]

df = pd.DataFrame(data)
print(f"Total verified observations: {len(df)}")
print(f"2016 Rules series: {len(df[df['comparability_group'] == 'CPCB_2016'])} obs")
print(f"2022 Rules series: {len(df[df['comparability_group'] == 'CPCB_2022'])} obs")

# ============================================================================
# 2. COMPUTE DERIVED FEATURES
# ============================================================================
print("\n2. COMPUTING DERIVED FEATURES")
print("-" * 40)

# Year-over-year growth (within same comparability group where sequential)
df['yoy_growth_tonnes'] = df['ewaste_generated_tonnes'].diff()
df['yoy_growth_pct'] = df['ewaste_generated_tonnes'].pct_change() * 100

# Flag the methodology break
df['framework_flag'] = (df['reporting_framework'] == '2022 Rules').astype(int)

# Time since start
df['years_since_start'] = df['year_index'] - 1

print(df[['financial_year', 'ewaste_generated_tonnes', 'yoy_growth_pct',
          'reporting_framework', 'framework_flag']].to_string(index=False))

print("\n  NOTE: YoY growth from 2022-23 to 2023-24 shows -22%.")
print("  This is NOT a real decline — it reflects the methodology change.")
print("  The 2022 Rules framework measures a different scope.")

# ============================================================================
# 3. CREATE MODELLING DATASETS
# ============================================================================
print("\n3. CREATING MODELLING DATASETS")
print("-" * 40)

# Dataset A: Full combined series (n=8) with framework flag
df_full = df[['financial_year', 'fy_start', 'year_index', 'years_since_start',
              'ewaste_generated_tonnes', 'ewaste_generated_kt', 'framework_flag',
              'reporting_framework', 'comparability_group', 'source_id',
              'record_id']].copy()
df_full.to_csv(os.path.join(PROCESSED_DIR, 'national_ewaste_full.csv'), index=False)
print(f"  Full dataset (n={len(df_full)}): national_ewaste_full.csv")

# Dataset B: 2016 Rules series only (n=6) — fully comparable
df_2016 = df[df['comparability_group'] == 'CPCB_2016'].copy()
df_2016.to_csv(os.path.join(PROCESSED_DIR, 'national_ewaste_2016rules.csv'), index=False)
print(f"  2016 Rules only (n={len(df_2016)}): national_ewaste_2016rules.csv")

# Dataset C: 2022 Rules series only (n=2) — too few for modelling alone
df_2022 = df[df['comparability_group'] == 'CPCB_2022'].copy()
df_2022.to_csv(os.path.join(PROCESSED_DIR, 'national_ewaste_2022rules.csv'), index=False)
print(f"  2022 Rules only (n={len(df_2022)}): national_ewaste_2022rules.csv")

# ============================================================================
# 4. DEFINE TRAIN/TEST SPLITS (CHRONOLOGICAL)
# ============================================================================
print("\n4. TRAIN/TEST SPLIT DESIGN (CHRONOLOGICAL)")
print("-" * 40)

print("""
  EVALUATION STRATEGY:
  Given only 8 observations, we use two complementary approaches:

  A) Leave-Last-Out Holdout:
     Train: First 6 observations (FY 2017-18 to FY 2022-23)
     Test:  Last 2 observations (FY 2023-24 to FY 2024-25)
     Note: Test set crosses the methodology boundary.

  B) Rolling-Origin (Expanding Window):
     Window 1: Train on obs 1-4, predict obs 5
     Window 2: Train on obs 1-5, predict obs 6
     Window 3: Train on obs 1-6, predict obs 7
     Window 4: Train on obs 1-7, predict obs 8
     This gives 4 one-step-ahead forecast errors.

  C) 2016 Rules Series Only (n=6):
     Train: obs 1-4, Test: obs 5-6
     Rolling: Train 1-3 predict 4; 1-4 predict 5; 1-5 predict 6

  No random splitting — this is time series data.
""")

# Save historical data for Power BI
hist_csv = os.path.join(PBI_DIR, 'historical_data.csv')
df_full.to_csv(hist_csv, index=False)
print(f"  Saved Power BI historical data: {hist_csv}")

# ============================================================================
# 5. EXTERNAL BENCHMARKS (separate file, NOT training data)
# ============================================================================
print("\n5. SAVING EXTERNAL BENCHMARKS (NOT TRAINING DATA)")
print("-" * 40)

benchmarks = [
    {'benchmark_id': 'B001', 'year': 2022, 'period_basis': 'Calendar year',
     'value_tonnes': 4137000, 'value_kt': 4137, 'data_type': 'International estimate',
     'source': 'Global E-waste Statistics Partnership',
     'note': 'NOT comparable to CPCB FY series'},
    {'benchmark_id': 'B002', 'year': 2020, 'period_basis': 'Calendar year',
     'value_tonnes': 2760000, 'value_kt': 2760, 'data_type': 'NITI Aayog cited estimate',
     'source': 'NITI Aayog report',
     'note': 'Secondary estimate; methodology differs from CPCB'},
    {'benchmark_id': 'B003', 'year': 2024, 'period_basis': 'Calendar year',
     'value_tonnes': 6190000, 'value_kt': 6190, 'data_type': 'NITI Aayog cited estimate',
     'source': 'NITI Aayog report',
     'note': 'Estimate, NOT observed data'},
    {'benchmark_id': 'B004', 'year': 2030, 'period_basis': 'Calendar year',
     'value_tonnes': 14000000, 'value_kt': 14000, 'data_type': 'Projection',
     'source': 'NITI Aayog 2030 projection',
     'note': 'NEVER use as observed training data'},
]
df_bench_out = pd.DataFrame(benchmarks)
df_bench_out.to_csv(os.path.join(PROCESSED_DIR, 'external_benchmarks.csv'), index=False)
print(f"  Saved: external_benchmarks.csv (for context/validation ONLY)")

# ============================================================================
# 6. DATA DICTIONARY
# ============================================================================
print("\n6. DATA DICTIONARY")
print("-" * 40)

data_dict = {
    'Column': [
        'financial_year', 'fy_start', 'year_index', 'years_since_start',
        'ewaste_generated_tonnes', 'ewaste_generated_kt', 'framework_flag',
        'reporting_framework', 'comparability_group', 'source_id', 'record_id'
    ],
    'Type': [
        'string', 'integer', 'integer', 'integer',
        'float', 'float', 'integer (0/1)',
        'string', 'string', 'string', 'string'
    ],
    'Description': [
        'Indian financial year (e.g. 2017-18 = Apr 2017 to Mar 2018)',
        'Calendar year in which the financial year starts',
        'Ordinal time index (1 = first observation)',
        'Years elapsed since first observation (0-based)',
        'E-waste generated in India, in tonnes (metric tonnes)',
        'E-waste generated in India, in kilotonnes (1 kt = 1000 tonnes)',
        'Binary: 0 = 2016 Rules framework, 1 = 2022 Rules framework',
        'Name of the regulatory framework under which the figure was reported',
        'Comparability group identifier for time-series continuity',
        'Reference to source publication (see source_register.csv)',
        'Unique record identifier'
    ],
    'Unit': [
        'N/A', 'year', 'ordinal', 'years',
        'tonnes', 'kt', 'binary',
        'N/A', 'N/A', 'N/A', 'N/A'
    ]
}
df_dict = pd.DataFrame(data_dict)
df_dict.to_csv(os.path.join(PROCESSED_DIR, 'data_dictionary.csv'), index=False)
print(df_dict.to_string(index=False))

print("\n" + "=" * 80)
print("DATA PREPARATION COMPLETE")
print("=" * 80)

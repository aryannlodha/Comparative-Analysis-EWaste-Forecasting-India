"""
generate_interactive_dashboard.py
=================================
Compiles an interactive standalone HTML5/Bootstrap/Chart.js decision-support dashboard
from the generated Power BI CSV files.

Pages:
  1. E-Waste Overview
  2. Forecast Comparison
  3. Model Performance
  4. Model Reliability
  5. Planning Insights
"""

import os
import json
import pandas as pd

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PBI_DIR = os.path.join(PROJECT_DIR, 'outputs', 'power_bi')
DASHBOARD_PATH = os.path.join(PROJECT_DIR, 'outputs', 'dashboard', 'index.html')

# Load data
df_hist = pd.read_csv(os.path.join(PBI_DIR, 'historical_data.csv'))
df_forecast = pd.read_csv(os.path.join(PBI_DIR, 'forecast_results.csv'))
df_metrics = pd.read_csv(os.path.join(PBI_DIR, 'model_metrics.csv'))
df_preds = pd.read_csv(os.path.join(PBI_DIR, 'model_predictions.csv'))
df_robust = pd.read_csv(os.path.join(PBI_DIR, 'model_robustness_results.csv'))
df_quality = pd.read_csv(os.path.join(PBI_DIR, 'data_quality_report.csv'))
df_sources = pd.read_csv(os.path.join(PBI_DIR, 'source_register.csv'))

# Prepare JSON blobs
hist_json = df_hist.to_dict(orient='records')
forecast_json = df_forecast.to_dict(orient='records')
metrics_json = df_metrics.to_dict(orient='records')
preds_json = df_preds.to_dict(orient='records')
robust_json = df_robust.to_dict(orient='records')
quality_json = df_quality.to_dict(orient='records')
sources_json = df_sources.to_dict(orient='records')

html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>EIS Decision Support Dashboard | E-Waste Forecasting India</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css">
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <style>
    body {{ background-color: #f4f6f9; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; }}
    .navbar-brand {{ font-weight: 700; letter-spacing: -0.5px; }}
    .card {{ border: none; border-radius: 10px; box-shadow: 0 0.125rem 0.25rem rgba(0,0,0,0.075); margin-bottom: 20px; }}
    .kpi-card {{ border-left: 4px solid #0d6efd; transition: transform 0.2s; }}
    .kpi-card:hover {{ transform: translateY(-3px); }}
    .kpi-title {{ font-size: 0.85rem; color: #6c757d; font-weight: 600; text-transform: uppercase; }}
    .kpi-value {{ font-size: 1.8rem; font-weight: 700; color: #212529; }}
    .kpi-subtext {{ font-size: 0.8rem; color: #8c98a4; }}
    .badge-fw1 {{ background-color: #0d6efd; }}
    .badge-fw2 {{ background-color: #fd7e14; }}
    .nav-tabs .nav-link {{ color: #495057; font-weight: 600; border-radius: 8px 8px 0 0; padding: 12px 20px; }}
    .nav-tabs .nav-link.active {{ background-color: #ffffff; color: #0d6efd; border-bottom: 3px solid #0d6efd; }}
    .chart-container {{ position: relative; height: 380px; width: 100%; }}
    .table-sm th, .table-sm td {{ font-size: 0.88rem; vertical-align: middle; }}
    .disclaimer-box {{ border-left: 4px solid #ffc107; background-color: #fff9e6; padding: 15px; border-radius: 6px; font-size: 0.9rem; }}
  </style>
</head>
<body>

<nav class="navbar navbar-dark bg-dark sticky-top px-4 py-2 shadow-sm">
  <div class="container-fluid d-flex justify-content-between align-items-center">
    <span class="navbar-brand d-flex align-items-center gap-2">
      <i class="bi bi-cpu text-info"></i>
      Enterprise Information Systems: E-Waste Decision Support System
    </span>
    <span class="badge bg-secondary">India Forecasting Model Comparison</span>
  </div>
</nav>

<div class="container-fluid px-4 py-3">
  <!-- Title & Meta Banner -->
  <div class="d-flex justify-content-between align-items-center pb-2 mb-3 border-bottom">
    <div>
      <h3 class="h4 fw-bold text-dark mb-1">Comparative Analysis of Predictive Models for E-Waste Generation Forecasting in India</h3>
      <p class="text-muted small mb-0">EIS Academic Research Project | Decision-Support Dashboard & Validation Engine</p>
    </div>
    <div class="d-flex gap-2">
      <span class="badge bg-primary">Power BI Companion View</span>
      <span class="badge bg-success">Verified CPCB/PIB Data</span>
    </div>
  </div>

  <!-- Navigation Tabs -->
  <ul class="nav nav-tabs mb-4" id="dashboardTabs" role="tablist">
    <li class="nav-item" role="presentation">
      <button class="nav-link active" id="tab-overview" data-bs-toggle="tab" data-bs-target="#overview" type="button" role="tab">
        <i class="bi bi-graph-up me-1"></i> 1. E-Waste Overview
      </button>
    </li>
    <li class="nav-item" role="presentation">
      <button class="nav-link" id="tab-forecast" data-bs-toggle="tab" data-bs-target="#forecast" type="button" role="tab">
        <i class="bi bi-binoculars me-1"></i> 2. Forecast Comparison
      </button>
    </li>
    <li class="nav-item" role="presentation">
      <button class="nav-link" id="tab-performance" data-bs-toggle="tab" data-bs-target="#performance" type="button" role="tab">
        <i class="bi bi-bar-chart-steps me-1"></i> 3. Model Performance
      </button>
    </li>
    <li class="nav-item" role="presentation">
      <button class="nav-link" id="tab-reliability" data-bs-toggle="tab" data-bs-target="#reliability" type="button" role="tab">
        <i class="bi bi-shield-check me-1"></i> 4. Model Reliability
      </button>
    </li>
    <li class="nav-item" role="presentation">
      <button class="nav-link" id="tab-planning" data-bs-toggle="tab" data-bs-target="#planning" type="button" role="tab">
        <i class="bi bi-lightbulb me-1"></i> 5. Planning Insights
      </button>
    </li>
  </ul>

  <!-- Tab Content -->
  <div class="tab-content" id="dashboardTabContent">
    
    <!-- PAGE 1: OVERVIEW -->
    <div class="tab-pane fade show active" id="overview" role="tabpanel">
      <!-- Top KPIs -->
      <div class="row g-3 mb-4">
        <div class="col-md-3">
          <div class="card p-3 kpi-card" style="border-left-color: #0d6efd;">
            <div class="kpi-title">Latest Verified Generation</div>
            <div class="kpi-value text-primary">1,397,956 MT</div>
            <div class="kpi-subtext">FY 2024–25 (2022 Rules, PIB S02)</div>
          </div>
        </div>
        <div class="col-md-3">
          <div class="card p-3 kpi-card" style="border-left-color: #6f42c1;">
            <div class="kpi-title">Peak 2016 Rules Generation</div>
            <div class="kpi-value text-dark">1,609,117 MT</div>
            <div class="kpi-subtext">FY 2022–23 (Old Framework baseline)</div>
          </div>
        </div>
        <div class="col-md-3">
          <div class="card p-3 kpi-card" style="border-left-color: #fd7e14;">
            <div class="kpi-title">Regulatory Frameworks</div>
            <div class="kpi-value text-warning">2 Eras</div>
            <div class="kpi-subtext">2016 Rules (21 EEE) vs 2022 (106 EEE)</div>
          </div>
        </div>
        <div class="col-md-3">
          <div class="card p-3 kpi-card" style="border-left-color: #198754;">
            <div class="kpi-title">Total Verified Observations</div>
            <div class="kpi-value text-success">8 Years</div>
            <div class="kpi-subtext">FY 2017–18 through FY 2024–25</div>
          </div>
        </div>
      </div>

      <!-- Main Overview Chart & Breakdown -->
      <div class="row g-3">
        <div class="col-lg-8">
          <div class="card p-4">
            <h5 class="fw-bold mb-3"><i class="bi bi-clock-history me-2"></i>Historical National E-Waste Generation (India)</h5>
            <div class="chart-container">
              <canvas id="overviewChart"></canvas>
            </div>
            <div class="mt-3 small text-muted">
              <span class="badge badge-fw1 me-1">Blue</span> 2016 Rules Series (FY 2017–18 to FY 2022–23, 21 EEE types) | 
              <span class="badge badge-fw2 me-1">Orange</span> 2022 Rules Series (FY 2023–24 onwards, registered producer basis)
            </div>
          </div>
        </div>
        <div class="col-lg-4">
          <div class="card p-4">
            <h5 class="fw-bold mb-3"><i class="bi bi-database-check me-2"></i>Verified Historical Records</h5>
            <div class="table-responsive">
              <table class="table table-sm table-hover" id="overviewTable">
                <thead class="table-light">
                  <tr>
                    <th>FY</th>
                    <th>Tonnes (MT)</th>
                    <th>YoY</th>
                    <th>Framework</th>
                  </tr>
                </thead>
                <tbody></tbody>
              </table>
            </div>
            <div class="disclaimer-box mt-2">
              <strong>Methodology Break Note:</strong> The drop from FY 2022–23 (1.61M MT) to FY 2023–24 (1.25M MT) reflects a transition to registered producer sales under the 2022 Rules, not a true consumption collapse.
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- PAGE 2: FORECAST COMPARISON -->
    <div class="tab-pane fade" id="forecast" role="tabpanel">
      <div class="row g-3 mb-3">
        <div class="col-12">
          <div class="card p-4">
            <div class="d-flex justify-content-between align-items-center mb-3">
              <h5 class="fw-bold mb-0"><i class="bi bi-graph-up-arrow me-2"></i>Comparative Forecast Trajectories Through FY 2030–31</h5>
              <div class="d-flex align-items-center gap-2">
                <label class="small fw-semibold text-muted">Model View:</label>
                <select class="form-select form-select-sm" id="forecastModelFilter" style="width: 220px;" onchange="updateForecastChart()">
                  <option value="ALL">Show All Models</option>
                  <option value="Linear Regression (FW)">Linear Regression (FW)</option>
                  <option value="Linear Regression">Linear Regression (Standard)</option>
                  <option value="ARIMA(1,1,0)">ARIMA(1,1,0)</option>
                  <option value="Gaussian Process">Gaussian Process</option>
                  <option value="Random Forest">Random Forest</option>
                  <option value="XGBoost">XGBoost</option>
                  <option value="Naive Baseline">Naive Baseline</option>
                </select>
              </div>
            </div>
            <div class="chart-container" style="height: 420px;">
              <canvas id="forecastChart"></canvas>
            </div>
          </div>
        </div>
      </div>

      <div class="row g-3">
        <div class="col-12">
          <div class="card p-4">
            <h5 class="fw-bold mb-3"><i class="bi bi-table me-2"></i>Multi-Model Forecast Matrix (Tonnes)</h5>
            <div class="table-responsive">
              <table class="table table-sm table-bordered text-center" id="forecastMatrixTable">
                <thead class="table-dark">
                  <tr>
                    <th>FY</th>
                    <th>Naive</th>
                    <th>LinReg</th>
                    <th>LinReg (FW)</th>
                    <th>ARIMA</th>
                    <th>Random Forest</th>
                    <th>XGBoost</th>
                    <th>Gaussian Process (Mean)</th>
                    <th>GP 95% Band</th>
                  </tr>
                </thead>
                <tbody></tbody>
              </table>
            </div>
            <div class="alert alert-info py-2 px-3 small mt-2 mb-0">
              <i class="bi bi-info-circle-fill me-1"></i> <strong>Critical Model Caveat:</strong> Tree ensembles (RF, XGBoost) lack natural extrapolation ability on small univariate time indices, causing them to plateau at the last training level (~1.43M MT). Linear Regression (FW) explicitly adjusts for the framework shift, extrapolating to 2.67M MT by 2030.
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- PAGE 3: MODEL PERFORMANCE -->
    <div class="tab-pane fade" id="performance" role="tabpanel">
      <div class="row g-3 mb-4">
        <div class="col-md-3">
          <div class="card p-3 kpi-card" style="border-left-color: #198754;">
            <div class="kpi-title">Lowest Rolling MAE</div>
            <div class="kpi-value text-success">190,280 MT</div>
            <div class="kpi-subtext">Naive Baseline (Walk-forward fold)</div>
          </div>
        </div>
        <div class="col-md-3">
          <div class="card p-3 kpi-card" style="border-left-color: #0d6efd;">
            <div class="kpi-title">Lowest Non-Trivial MAE</div>
            <div class="kpi-value text-primary">214,388 MT</div>
            <div class="kpi-subtext">ARIMA(1,1,0) (15.5% MAPE)</div>
          </div>
        </div>
        <div class="col-md-3">
          <div class="card p-3 kpi-card" style="border-left-color: #0dcaf0;">
            <div class="kpi-title">Framework Model MAE</div>
            <div class="kpi-value text-info">251,994 MT</div>
            <div class="kpi-subtext">LinReg (FW Adjusted, 18.7% MAPE)</div>
          </div>
        </div>
        <div class="col-md-3">
          <div class="card p-3 kpi-card" style="border-left-color: #dc3545;">
            <div class="kpi-title">Validation Folds</div>
            <div class="kpi-value text-danger">4 Origins</div>
            <div class="kpi-subtext">Rolling-origin (Train 4..7, Test 5..8)</div>
          </div>
        </div>
      </div>

      <div class="row g-3">
        <div class="col-lg-6">
          <div class="card p-4">
            <h5 class="fw-bold mb-3"><i class="bi bi-bar-chart-fill me-2"></i>Mean Absolute Error (MAE in Tonnes)</h5>
            <div class="chart-container">
              <canvas id="maeChart"></canvas>
            </div>
          </div>
        </div>
        <div class="col-lg-6">
          <div class="card p-4">
            <h5 class="fw-bold mb-3"><i class="bi bi-percent me-2"></i>Percentage Error Metrics (MAPE & sMAPE)</h5>
            <div class="chart-container">
              <canvas id="mapeChart"></canvas>
            </div>
          </div>
        </div>
      </div>

      <div class="row g-3 mt-1">
        <div class="col-12">
          <div class="card p-4">
            <h5 class="fw-bold mb-3"><i class="bi bi-list-check me-2"></i>Comprehensive Statistical Evaluation Table</h5>
            <div class="table-responsive">
              <table class="table table-sm table-striped" id="metricsTable">
                <thead class="table-light">
                  <tr>
                    <th>Model</th>
                    <th>Evaluation Method</th>
                    <th>Test Folds</th>
                    <th>MAE (MT)</th>
                    <th>RMSE (MT)</th>
                    <th>MAPE (%)</th>
                    <th>sMAPE (%)</th>
                    <th>Extrapolation Suitability</th>
                  </tr>
                </thead>
                <tbody></tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- PAGE 4: MODEL RELIABILITY -->
    <div class="tab-pane fade" id="reliability" role="tabpanel">
      <div class="row g-3 mb-4">
        <div class="col-lg-6">
          <div class="card p-4">
            <h5 class="fw-bold mb-2"><i class="bi bi-slash-circle me-2"></i>Exp A: Sensitivity to Training History Size</h5>
            <p class="text-muted small">Evaluating Linear Regression holdout error under truncated historical windows.</p>
            <div class="chart-container">
              <canvas id="expAChart"></canvas>
            </div>
            <div class="small text-muted mt-2">
              <strong>Observation:</strong> Training on fewer points before the structural break produces smaller post-break errors purely because older growth was steep and extrapolated even higher.
            </div>
          </div>
        </div>
        <div class="col-lg-6">
          <div class="card p-4">
            <h5 class="fw-bold mb-2"><i class="bi bi-dice-5 me-2"></i>Exp C: Gaussian Noise Perturbation</h5>
            <p class="text-muted small">Testing resilience against 5%, 10%, and 20% measurement noise (20 Monte Carlo iterations).</p>
            <div class="chart-container">
              <canvas id="expCChart"></canvas>
            </div>
            <div class="small text-muted mt-2">
              <strong>Observation:</strong> Linear regression remains structurally stable under mild noise (5%–10%), but variance spikes sharply at 20% perturbation.
            </div>
          </div>
        </div>
      </div>

      <div class="row g-3">
        <div class="col-lg-6">
          <div class="card p-4">
            <h5 class="fw-bold mb-2"><i class="bi bi-pie-chart me-2"></i>Exp B: Jackknife Drop-One Sensitivity</h5>
            <p class="text-muted small">Impact of removing individual historical observations on test set MAE.</p>
            <div class="chart-container">
              <canvas id="expBChart"></canvas>
            </div>
          </div>
        </div>
        <div class="col-lg-6">
          <div class="card p-4">
            <h5 class="fw-bold mb-2"><i class="bi bi-cone-striped me-2"></i>Exp D: Gaussian Process Forecast Uncertainty</h5>
            <p class="text-muted small">95% Bayesian credible interval expansion across the forecast horizon.</p>
            <div class="chart-container">
              <canvas id="expDChart"></canvas>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- PAGE 5: PLANNING INSIGHTS -->
    <div class="tab-pane fade" id="planning" role="tabpanel">
      <div class="row g-3 mb-4">
        <div class="col-lg-8">
          <div class="card p-4">
            <h5 class="fw-bold mb-3"><i class="bi bi-recycle me-2"></i>EIS Infrastructure & Recycling Capacity Gap (2030 Target)</h5>
            <div class="chart-container">
              <canvas id="planningChart"></canvas>
            </div>
          </div>
        </div>
        <div class="col-lg-4">
          <div class="card p-4">
            <h5 class="fw-bold mb-3"><i class="bi bi-sliders me-2"></i>Interactive Target Calculator</h5>
            <div class="mb-3">
              <label class="form-label small fw-bold">EPR Formal Collection Target (2030):</label>
              <div class="input-group input-group-sm">
                <input type="number" class="form-control" id="eprTargetRate" value="80" min="40" max="100">
                <span class="input-group-text">%</span>
              </div>
              <div class="form-text small">MoEFCC mandated target is 80% from 2027–28 onwards.</div>
            </div>
            <div class="mb-3">
              <label class="form-label small fw-bold">Select Forecast Scenario:</label>
              <select class="form-select form-select-sm" id="scenarioSelect" onchange="calcPlanning()">
                <option value="2674580">Linear Regression FW (2,674,580 MT)</option>
                <option value="2262371">Linear Regression Standard (2,262,371 MT)</option>
                <option value="1433882">ARIMA Conservative (1,433,882 MT)</option>
                <option value="6190000">NITI Aayog Benchmark (6,190,000 MT)</option>
              </select>
            </div>
            <hr>
            <div class="p-3 bg-light rounded">
              <div class="d-flex justify-content-between mb-2">
                <span class="small text-muted">Required Formal Collection:</span>
                <strong id="calcCollectionVal" class="text-primary">2,139,664 MT</strong>
              </div>
              <div class="d-flex justify-content-between">
                <span class="small text-muted">Uncollected / Informal Flow:</span>
                <strong id="calcUncollectedVal" class="text-danger">534,916 MT</strong>
              </div>
            </div>
            <button class="btn btn-sm btn-outline-primary w-100 mt-3" onclick="calcPlanning()">Re-calculate</button>
          </div>
        </div>
      </div>

      <!-- Qualitative Insights & Decision Rules -->
      <div class="row g-3">
        <div class="col-md-4">
          <div class="card p-3 h-100 border-start border-4 border-primary">
            <h6 class="fw-bold text-primary"><i class="bi bi-building me-1"></i> Processing Capacity Planning</h6>
            <p class="small text-muted mb-0">
              India's formal e-waste authorized capacity has expanded, but spatial concentration remains skewed towards Maharashtra, Gujarat, Tamil Nadu, and Haryana. Siting decisions for 2026–2030 must focus on Tier-2 collection logistics rather than expanding nominal plant count in saturated clusters.
            </p>
          </div>
        </div>
        <div class="col-md-4">
          <div class="card p-3 h-100 border-start border-4 border-warning">
            <h6 class="fw-bold text-warning"><i class="bi bi-exclamation-triangle me-1"></i> Data Scarcity Governance</h6>
            <p class="small text-muted mb-0">
              With only 8 national annual observations and inconsistent state-level disclosures, complex deep learning models are empirically indefensible. Enterprise systems must prioritize high-frequency telemetry from the CPCB EPR portal over complex statistical model selection.
            </p>
          </div>
        </div>
        <div class="col-md-4">
          <div class="card p-3 h-100 border-start border-4 border-success">
            <h6 class="fw-bold text-success"><i class="bi bi-check-circle me-1"></i> Regulatory Reconciliation</h6>
            <p class="small text-muted mb-0">
              The disparity between CPCB figures (~1.4 Mt) and international benchmarks (GEM: ~4.1 Mt) stems from accounting boundaries (producer sales tracking vs. consumption modeling). Decision-makers must not treat CPCB regulatory compliance numbers as total physical e-waste mass.
            </p>
          </div>
        </div>
      </div>
    </div>

  </div>
</div>

<script>
// Data Injected from Python
const histData = {json.dumps(hist_json)};
const forecastData = {json.dumps(forecast_json)};
const metricsData = {json.dumps(metrics_json)};
const robustData = {json.dumps(robust_json)};

// Populate Overview Table
const ovTable = document.querySelector('#overviewTable tbody');
histData.forEach((row, i) => {{
  const tr = document.createElement('tr');
  const yoyStr = row.yoy_growth_pct ? (row.yoy_growth_pct > 0 ? '+' : '') + row.yoy_growth_pct.toFixed(1) + '%' : '—';
  const badgeCls = row.reporting_framework === '2022 Rules' ? 'badge-fw2' : 'badge-fw1';
  tr.innerHTML = `
    <td><strong>${{row.financial_year}}</strong></td>
    <td>${{Number(row.ewaste_generated_tonnes).toLocaleString()}}</td>
    <td><span class="${{row.yoy_growth_pct < 0 ? 'text-danger' : 'text-success'}}">${{yoyStr}}</span></td>
    <td><span class="badge ${{badgeCls}}">${{row.reporting_framework}}</span></td>
  `;
  ovTable.appendChild(tr);
}});

// Overview Chart
new Chart(document.getElementById('overviewChart'), {{
  type: 'bar',
  data: {{
    labels: histData.map(d => d.financial_year),
    datasets: [{{
      label: 'Generation (Tonnes)',
      data: histData.map(d => d.ewaste_generated_tonnes),
      backgroundColor: histData.map(d => d.reporting_framework === '2022 Rules' ? '#fd7e14' : '#0d6efd'),
      borderRadius: 6
    }}]
  }},
  options: {{
    responsive: true,
    maintainAspectRatio: false,
    plugins: {{
      legend: {{ display: false }},
      tooltip: {{
        callbacks: {{
          label: ctx => Number(ctx.raw).toLocaleString() + ' MT'
        }}
      }}
    }},
    scales: {{
      y: {{
        beginAtZero: true,
        title: {{ display: true, text: 'Metric Tonnes' }},
        ticks: {{ callback: val => (val/1e6).toFixed(1) + 'M' }}
      }}
    }}
  }}
}});

// Forecast Chart Initialization
let forecastChartInst = null;
function initForecastChart() {{
  const years = ['2017-18','2018-19','2019-20','2020-21','2021-22','2022-23','2023-24','2024-25','2025-26','2026-27','2027-28','2028-29','2029-30','2030-31'];
  
  // Historical mapping
  const actuals = years.map(yr => {{
    const h = histData.find(d => d.financial_year === yr);
    return h ? h.ewaste_generated_tonnes : null;
  }});

  const getSeries = (modelName) => {{
    return years.map(yr => {{
      const f = forecastData.find(d => d.model === modelName && d.financial_year === yr);
      return f ? f.forecast_tonnes : null;
    }});
  }};

  const datasets = [
    {{
      label: 'Historical Actual',
      data: actuals,
      borderColor: '#000000',
      backgroundColor: '#000000',
      borderWidth: 2.5,
      pointRadius: 4,
      tension: 0
    }},
    {{
      label: 'Linear Regression (FW)',
      data: getSeries('Linear Regression (FW)'),
      borderColor: '#0dcaf0',
      borderDash: [5, 5],
      pointRadius: 3,
      hidden: false
    }},
    {{
      label: 'Linear Regression',
      data: getSeries('Linear Regression'),
      borderColor: '#0d6efd',
      borderDash: [5, 5],
      pointRadius: 3,
      hidden: false
    }},
    {{
      label: 'ARIMA(1,1,0)',
      data: getSeries('ARIMA(1,1,0)'),
      borderColor: '#198754',
      borderDash: [5, 5],
      pointRadius: 3,
      hidden: false
    }},
    {{
      label: 'Gaussian Process',
      data: getSeries('Gaussian Process'),
      borderColor: '#dc3545',
      borderDash: [5, 5],
      pointRadius: 3,
      hidden: false
    }},
    {{
      label: 'Random Forest',
      data: getSeries('Random Forest'),
      borderColor: '#6f42c1',
      borderDash: [5, 5],
      pointRadius: 3,
      hidden: true
    }},
    {{
      label: 'XGBoost',
      data: getSeries('XGBoost'),
      borderColor: '#fd7e14',
      borderDash: [5, 5],
      pointRadius: 3,
      hidden: true
    }},
    {{
      label: 'Naive Baseline',
      data: getSeries('Naive Baseline'),
      borderColor: '#adb5bd',
      borderDash: [3, 3],
      pointRadius: 2,
      hidden: true
    }}
  ];

  forecastChartInst = new Chart(document.getElementById('forecastChart'), {{
    type: 'line',
    data: {{ labels: years, datasets: datasets }},
    options: {{
      responsive: true,
      maintainAspectRatio: false,
      plugins: {{
        tooltip: {{
          callbacks: {{
            label: ctx => ctx.dataset.label + ': ' + Number(ctx.raw).toLocaleString() + ' MT'
          }}
        }}
      }},
      scales: {{
        y: {{
          beginAtZero: true,
          title: {{ display: true, text: 'E-Waste Generated (Metric Tonnes)' }},
          ticks: {{ callback: val => (val/1e6).toFixed(1) + 'M' }}
        }}
      }}
    }}
  }});
}}

function updateForecastChart() {{
  const val = document.getElementById('forecastModelFilter').value;
  if (!forecastChartInst) return;
  forecastChartInst.data.datasets.forEach((ds, idx) => {{
    if (idx === 0) return; // keep actuals
    if (val === 'ALL') {{
      ds.hidden = (ds.label === 'Random Forest' || ds.label === 'XGBoost' || ds.label === 'Naive Baseline');
    }} else {{
      ds.hidden = (ds.label !== val);
    }}
  }});
  forecastChartInst.update();
}}

// Populate Forecast Matrix Table
const matrixTbody = document.querySelector('#forecastMatrixTable tbody');
const futureYears = ['2025-26', '2026-27', '2027-28', '2028-29', '2029-30', '2030-31'];
futureYears.forEach(yr => {{
  const getF = (m) => {{
    const r = forecastData.find(d => d.model === m && d.financial_year === yr);
    return r ? Math.round(r.forecast_tonnes).toLocaleString() : '—';
  }};
  const gp = forecastData.find(d => d.model === 'Gaussian Process' && d.financial_year === yr);
  const band = gp && gp.gp_95ci_low ? `[${{Math.round(gp.gp_95ci_low).toLocaleString()}}, ${{Math.round(gp.gp_95ci_high).toLocaleString()}}]` : '—';
  const tr = document.createElement('tr');
  tr.innerHTML = `
    <td><strong>${{yr}}</strong></td>
    <td>${{getF('Naive Baseline')}}</td>
    <td>${{getF('Linear Regression')}}</td>
    <td class="table-info fw-bold">${{getF('Linear Regression (FW)')}}</td>
    <td>${{getF('ARIMA(1,1,0)')}}</td>
    <td>${{getF('Random Forest')}}</td>
    <td>${{getF('XGBoost')}}</td>
    <td class="text-danger">${{getF('Gaussian Process')}}</td>
    <td class="small text-muted">${{band}}</td>
  `;
  matrixTbody.appendChild(tr);
}});

// Metrics Charts & Table
const metricsSorted = [...metricsData].sort((a,b) => a.MAE_tonnes - b.MAE_tonnes);

new Chart(document.getElementById('maeChart'), {{
  type: 'bar',
  data: {{
    labels: metricsSorted.map(m => m.Model),
    datasets: [{{
      label: 'MAE (Tonnes)',
      data: metricsSorted.map(m => m.MAE_tonnes),
      backgroundColor: '#0d6efd',
      borderRadius: 5
    }}]
  }},
  options: {{
    indexAxis: 'y',
    responsive: true,
    maintainAspectRatio: false,
    plugins: {{ legend: {{ display: false }} }}
  }}
}});

new Chart(document.getElementById('mapeChart'), {{
  type: 'bar',
  data: {{
    labels: metricsSorted.map(m => m.Model),
    datasets: [
      {{ label: 'MAPE (%)', data: metricsSorted.map(m => m.MAPE_pct), backgroundColor: '#198754', borderRadius: 4 }},
      {{ label: 'sMAPE (%)', data: metricsSorted.map(m => m.sMAPE_pct), backgroundColor: '#20c997', borderRadius: 4 }}
    ]
  }},
  options: {{
    indexAxis: 'y',
    responsive: true,
    maintainAspectRatio: false
  }}
}});

const mTable = document.querySelector('#metricsTable tbody');
metricsSorted.forEach(m => {{
  const tr = document.createElement('tr');
  let suit = '<span class="badge bg-success">Suitable</span>';
  if (m.Model.includes('Random Forest') || m.Model.includes('XGBoost')) {{
    suit = '<span class="badge bg-danger">Cannot Extrapolate</span>';
  }} else if (m.Model.includes('Gaussian Process')) {{
    suit = '<span class="badge bg-warning text-dark">High Divergence</span>';
  }}
  tr.innerHTML = `
    <td><strong>${{m.Model}}</strong></td>
    <td>${{m.Eval_Method}}</td>
    <td>${{m.N_Test_Obs}}</td>
    <td>${{Number(m.MAE_tonnes).toLocaleString()}}</td>
    <td>${{Number(m.RMSE_tonnes).toLocaleString()}}</td>
    <td>${{m.MAPE_pct}}%</td>
    <td>${{m.sMAPE_pct}}%</td>
    <td>${{suit}}</td>
  `;
  mTable.appendChild(tr);
}});

// Robustness Charts
const expA = robustData.filter(d => d.experiment === 'A_limited_training');
new Chart(document.getElementById('expAChart'), {{
  type: 'bar',
  data: {{
    labels: expA.map(d => d.config),
    datasets: [{{
      label: 'MAE (Tonnes)',
      data: expA.map(d => d.MAE_tonnes),
      backgroundColor: '#6f42c1',
      borderRadius: 5
    }}]
  }},
  options: {{ responsive: true, maintainAspectRatio: false }}
}});

const expC = robustData.filter(d => d.experiment === 'C_noise');
new Chart(document.getElementById('expCChart'), {{
  type: 'bar',
  data: {{
    labels: expC.map(d => d.config),
    datasets: [{{
      label: 'Mean MAE (Tonnes)',
      data: expC.map(d => d.MAE_tonnes),
      backgroundColor: '#fd7e14',
      borderRadius: 5
    }}]
  }},
  options: {{ responsive: true, maintainAspectRatio: false }}
}});

const expB = robustData.filter(d => d.experiment === 'B_missing_obs');
new Chart(document.getElementById('expBChart'), {{
  type: 'bar',
  data: {{
    labels: expB.map(d => d.config.replace('Drop ', '')),
    datasets: [{{
      label: 'Holdout MAE (Tonnes)',
      data: expB.map(d => d.MAE_tonnes),
      backgroundColor: '#0dcaf0',
      borderRadius: 5
    }}]
  }},
  options: {{ responsive: true, maintainAspectRatio: false }}
}});

const expD = robustData.filter(d => d.experiment === 'D_uncertainty');
new Chart(document.getElementById('expDChart'), {{
  type: 'line',
  data: {{
    labels: expD.map(d => d.config.replace('FY ', '')),
    datasets: [{{
      label: 'GP Predictive Std (Tonnes)',
      data: expD.map(d => d.RMSE_tonnes),
      borderColor: '#dc3545',
      backgroundColor: 'rgba(220,53,69,0.1)',
      fill: true,
      tension: 0.2
    }}]
  }},
  options: {{ responsive: true, maintainAspectRatio: false }}
}});

// Planning Chart
new Chart(document.getElementById('planningChart'), {{
  type: 'bar',
  data: {{
    labels: ['2024-25 Baseline', '2030 (ARIMA)', '2030 (LinReg Std)', '2030 (LinReg FW)', '2030 (NITI Projection)'],
    datasets: [{{
      label: 'E-Waste Quantity (Million MT)',
      data: [1.398, 1.434, 2.262, 2.675, 14.0],
      backgroundColor: ['#6c757d', '#198754', '#0d6efd', '#0dcaf0', '#dc3545'],
      borderRadius: 6
    }}]
  }},
  options: {{
    responsive: true,
    maintainAspectRatio: false,
    plugins: {{
      tooltip: {{ callbacks: {{ label: ctx => ctx.raw + ' Million Metric Tonnes' }} }}
    }}
  }}
}});

function calcPlanning() {{
  const gen = Number(document.getElementById('scenarioSelect').value);
  const rate = Number(document.getElementById('eprTargetRate').value) / 100;
  const col = Math.round(gen * rate);
  const uncol = Math.round(gen * (1 - rate));
  document.getElementById('calcCollectionVal').innerText = col.toLocaleString() + ' MT';
  document.getElementById('calcUncollectedVal').innerText = uncol.toLocaleString() + ' MT';
}}

// Initialize charts on tab shown
document.addEventListener('DOMContentLoaded', () => {{
  initForecastChart();
  calcPlanning();
}});
</script>

<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""

with open(DASHBOARD_PATH, 'w', encoding='utf-8') as f:
    f.write(html_content)

print(f"Interactive dashboard successfully generated at: {DASHBOARD_PATH}")

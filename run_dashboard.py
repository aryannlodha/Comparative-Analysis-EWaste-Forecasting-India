"""
run_dashboard.py
================
Launches the interactive EIS Decision-Support Dashboard in the default web browser.
"""

import os
import sys
import webbrowser

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
DASHBOARD_FILE = os.path.join(PROJECT_DIR, 'outputs', 'dashboard', 'index.html')

if not os.path.exists(DASHBOARD_FILE):
    # Try src/ parent
    DASHBOARD_FILE = os.path.join(os.path.dirname(PROJECT_DIR), 'outputs', 'dashboard', 'index.html')

if os.path.exists(DASHBOARD_FILE):
    print(f"Opening Decision-Support Dashboard: {DASHBOARD_FILE}")
    webbrowser.open(f"file:///{os.path.abspath(DASHBOARD_FILE).replace(os.sep, '/')}")
else:
    print(f"Error: Dashboard file not found at {DASHBOARD_FILE}")
    sys.exit(1)

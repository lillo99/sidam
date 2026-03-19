#!/bin/bash
# Avvia la Web App Sidam - doppio clic per aprire
cd "$(dirname "$0")"
.venv/bin/streamlit run app.py --server.headless false --browser.gatherUsageStats false

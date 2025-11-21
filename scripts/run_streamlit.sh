#!/bin/bash
# Script pour lancer l'application Streamlit
cd "$(dirname "$0")/.."
streamlit run src/streamlit_app.py --server.port 8501 --server.address 0.0.0.0


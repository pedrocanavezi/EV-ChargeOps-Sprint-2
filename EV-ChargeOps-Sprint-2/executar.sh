#!/usr/bin/env sh
set -eu
python -c "import streamlit, pandas" 2>/dev/null || python -m pip install -r requirements.txt
python -m streamlit run app.py


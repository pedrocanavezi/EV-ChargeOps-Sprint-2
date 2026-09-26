@echo off
title EV ChargeOps
echo Preparando o EV ChargeOps...
python -c "import streamlit, pandas" 2>NUL || python -m pip install -r requirements.txt
python -m streamlit run app.py
pause


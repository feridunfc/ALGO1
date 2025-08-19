
Usage (Windows PowerShell):

1) Install deps:
   pip install -r ui_v1_1\requirements.txt

2) Ensure backend 'src' is sibling of 'ui_v1_1' and importable:
   $env:PYTHONPATH = "$PWD\src"

3) Run:
   streamlit run ui_v1_1\streamlit_app.py

Notes:
- Optuna tuner demo works for 'ma_crossover' strategy (Sharpe maximize).
- Orchestrator must exist at src/pipeline/orchestrator.py
- Output artifacts are written to the chosen out_dir.

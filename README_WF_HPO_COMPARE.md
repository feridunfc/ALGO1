# WF/HPO Batch Integration + Compare Page Hotfix (v2.6)
This patch adds:
- WalkForwardEngine with Sharpe/MaxDD/WinRate/Turnover metrics
- HPOEngine with Optuna + MedianPruner (fold-wise pruning)
- UI Compare page that runs WF across selected strategies, shows a sortable table, and exports CSV
- Batch runner service (run_wf_batch, run_hpo)

## Quick start
pip install pandas numpy scikit-learn optuna streamlit pytest
pytest -q tests/smoke/test_wf_engine_smoke.py
streamlit run ui/pages/compare.py

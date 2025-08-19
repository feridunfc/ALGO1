# Models Pack Hotfix (v2.6)
Adds **10 AI + 10 Rule-based + 5 Hybrid** strategies with a unified `Strategy` API.
- Registered in `src/strategies/registry.py`.
- Smoke test ensures every strategy returns `predict_proba` in [0,1].
- Simple runner at `ui/services/run_model.py`.

## Install
pip install pandas numpy scikit-learn optuna pytest
# (optional) xgboost lightgbm catboost torch

## Test
pytest -q tests/smoke/test_registry_and_predict.py

## Use
from ui.services.run_model import run
res = run("hy_ensemble_voter")

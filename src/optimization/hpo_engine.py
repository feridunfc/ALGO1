# src/optimization/hpo_engine.py
from typing import Type
import numpy as np, pandas as pd, optuna, json
from pathlib import Path
from ..strategies.base import Strategy
from ..strategies.xgboost_strategy import XGBoostStrategy
from ..backtest.wf_engine import WalkForwardEngine, BacktestEngine

class HPOEngine:
    def __init__(self, storage: str = "sqlite:///hpo.db"):
        self.storage = storage
        cfg = json.loads(Path("config/config.json").read_text())
        self.metric_key = cfg.get("HPO_METRIC", "sharpe")
        self.n_trials = int(cfg.get("HPO_TRIALS", 50))
        self.timeout = int(cfg.get("HPO_TIMEOUT", 0))

    def _metric_from_report(self, report) -> float:
        agg = report.aggregate()
        return float(agg.get(self.metric_key, 0.0))

    def optimize(self, strategy_class: Type[Strategy], data: pd.DataFrame):
        study = optuna.create_study(direction="maximize", storage=self.storage, load_if_exists=True,
                                    study_name=f"{strategy_class.__name__}_v2_6")
        def objective(trial):
            params = strategy_class.suggest_hyperparameters(trial)
            strat = strategy_class(**params)
            wf = WalkForwardEngine(BacktestEngine)
            rep = wf.run(strat, data)
            return self._metric_from_report(rep)

        study.optimize(objective, n_trials=self.n_trials, timeout=(self.timeout if self.timeout>0 else None))
        # Save best params
        best = {"strategy": strategy_class.__name__, "best_params": study.best_params}
        Path("artifacts").mkdir(parents=True, exist_ok=True)
        Path(f"artifacts/{strategy_class.__name__}_best.json").write_text(json.dumps(best, indent=2))
        return study

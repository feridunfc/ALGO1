from __future__ import annotations
import numpy as np
import pandas as pd
from typing import Callable, Dict, Any, Optional
try:
    import optuna
except Exception:  # Optuna opsiyonel
    optuna = None

class HPOStudy:
    def __init__(self, runner, strategy_factory: Callable[..., Any], features: pd.DataFrame, prices: pd.Series):
        self.runner = runner
        self.strategy_factory = strategy_factory
        self.features = features
        self.prices = prices

    def optimize(self, search_space: Callable, n_trials: int = 25, direction: str = "maximize") -> Dict[str, Any]:
        if optuna is None:
            return {"error": "optuna_not_installed", "message": "Install optuna to use HPO."}
        def objective(trial):
            params = search_space(trial)
            df, summary = self.runner.run(self.features, self.prices, self.strategy_factory, params)
            return summary.get("mean_sharpe", 0.0)
        study = optuna.create_study(direction=direction)
        study.optimize(objective, n_trials=n_trials, show_progress_bar=False)
        return {"best_params": study.best_trial.params, "best_value": study.best_value}

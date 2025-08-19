import optuna
import numpy as np
import pandas as pd
from typing import Callable, Dict, Any, Optional
from sklearn.model_selection import TimeSeriesSplit

from ..src.backtest.wf_engine import WalkForwardEngine
from ..src.strategies.registry import STRATEGY_REGISTRY

PARAM_SPECS = {
    "ai_random_forest": lambda t: {"n_estimators": t.suggest_int("n_estimators", 100, 600),
                                   "max_depth": t.suggest_int("max_depth", 3, 12)},
    "ai_tree_boost": lambda t: {"n_estimators": t.suggest_int("n_estimators", 100, 500),
                                "max_depth": t.suggest_int("max_depth", 3, 10),
                                "learning_rate": t.suggest_float("learning_rate", 1e-3, 0.2, log=True)},
    "rb_ma_crossover": lambda t: {"fast": t.suggest_int("fast", 5, 50),
                                  "slow": t.suggest_int("slow", 30, 200)},
    "rb_breakout": lambda t: {"lookback": t.suggest_int("lookback", 10, 60)},
}

def suggest_params(strategy_key: str, trial: optuna.trial.Trial) -> dict:
    fn = PARAM_SPECS.get(strategy_key, None)
    if fn is None: return {}
    return fn(trial)

class HPOEngine:
    def __init__(self, wf_splits=5, wf_test=63, metric="sharpe",
                 n_startup=5, warmup_steps=1, storage: Optional[str] = None):
        self.metric = metric
        self.wf = WalkForwardEngine(n_splits=wf_splits, test_size=wf_test)
        self.storage = storage
        self.pruner = optuna.pruners.MedianPruner(n_startup_trials=n_startup, n_warmup_steps=warmup_steps)

    def optimize(self, strategy_key: str, data: pd.DataFrame, n_trials=50, timeout=0):
        def objective(trial: optuna.trial.Trial):
            params = suggest_params(strategy_key, trial)
            Strat = STRATEGY_REGISTRY[strategy_key]
            strat = Strat(**params)

            # Manual fold loop with pruning feedback
            tscv = TimeSeriesSplit(n_splits=self.wf.n_splits, test_size=self.wf.test_size)
            scores = []
            fold_idx = 0
            for tr_idx, te_idx in tscv.split(data):
                df_train = data.iloc[tr_idx]
                df_test  = data.iloc[te_idx]
                if hasattr(strat, "fit"):
                    try: strat.fit(df_train)
                    except Exception: pass
                rep = self.wf.run(strat, df_test)
                val = rep.aggregate().get(self.metric, 0.0)
                scores.append(val)
                trial.report(np.mean(scores), fold_idx)
                if trial.should_prune():
                    raise optuna.TrialPruned()
                fold_idx += 1
            return float(np.mean(scores))

        study = optuna.create_study(direction="maximize", storage=self.storage,
                                    pruner=self.pruner, load_if_exists=False)
        study.optimize(objective, n_trials=n_trials, timeout=timeout if timeout and timeout>0 else None)
        return study

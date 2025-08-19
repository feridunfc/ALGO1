from typing import Type, Dict, List
import numpy as np
import pandas as pd
import optuna
from sklearn.model_selection import TimeSeriesSplit
from ..strategies.base import Strategy
try:
    from ..backtest.engine import BacktestEngine  # use real engine if present
except Exception:
    from ..backtest.wf_runner import BacktestEngine  # fallback no-op engine

def _sharpe(res) -> float:
    eq = getattr(res, "equity_curve", None)
    if eq is None or len(eq) < 2: return 0.0
    rets = eq.pct_change().dropna()
    if rets.std(ddof=0) == 0: return 0.0
    return float(np.sqrt(252) * rets.mean() / (rets.std(ddof=0) + 1e-12))

class OptunaOptimizer:
    def __init__(self, strategy_class: Type[Strategy], n_trials: int = 50, seed: int = 42,
                 n_splits: int = 5, test_size: int = 63, gap: int = 1,
                 pruner: optuna.pruners.BasePruner = None):
        self.strategy_class = strategy_class
        self.n_trials = n_trials
        self.seed = seed
        self.n_splits = n_splits
        self.test_size = test_size
        self.gap = gap
        # Default to MedianPruner for early stopping
        self.pruner = pruner or optuna.pruners.MedianPruner(n_startup_trials=8, n_warmup_steps=1)

    def optimize(self, data: pd.DataFrame):
        sampler = optuna.samplers.TPESampler(seed=self.seed)
        study = optuna.create_study(direction="maximize", sampler=sampler, pruner=self.pruner)
        study.optimize(lambda tr: self._objective(tr, data), n_trials=self.n_trials)
        return study

    def _objective(self, trial: optuna.Trial, data: pd.DataFrame):
        # Strategy param sampling
        params = self.strategy_class.suggest_params(trial)
        strategy = self.strategy_class(**params)

        # Manual WF loop to enable pruning per-fold
        tscv = TimeSeriesSplit(n_splits=self.n_splits, test_size=self.test_size, gap=self.gap)
        engine = BacktestEngine()

        fold_scores: List[float] = []
        for fold, (train_idx, test_idx) in enumerate(tscv.split(data)):
            train_df = data.iloc[train_idx]
            test_df  = data.iloc[test_idx]

            if hasattr(strategy, "fit"):
                strategy.fit(train_df)

            res = engine.run(data=test_df, strategy=strategy)
            score = _sharpe(res)
            fold_scores.append(score)

            # Report interim mean; enable pruning
            trial.report(float(np.mean(fold_scores)), step=fold)
            if trial.should_prune():
                raise optuna.exceptions.TrialPruned()

        return float(np.mean(fold_scores))

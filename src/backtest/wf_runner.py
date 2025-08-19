from dataclasses import dataclass, field
from typing import Dict, List, Optional
import numpy as np, pandas as pd
from sklearn.model_selection import TimeSeriesSplit

try:
    # Expecting an engine in src/backtest/engine.py
    from .engine import BacktestEngine
except Exception:
    class BacktestEngine:
        def run(self, data: pd.DataFrame, strategy):
            # Minimal placeholder result for smoke tests
            class Res:
                equity_curve = pd.Series(np.cumprod(1+0*data['close'].pct_change().fillna(0.0)), index=data.index)
                positions = pd.Series(0, index=data.index)
            return Res()

@dataclass
class FoldReport:
    fold: int
    metrics: Dict[str, float]

@dataclass
class WFResults:
    folds: List[FoldReport] = field(default_factory=list)
    def aggregate(self) -> Dict[str, float]:
        if not self.folds: return {}
        keys = self.folds[0].metrics.keys()
        return {k: float(np.nanmean([f.metrics[k] for f in self.folds])) for k in keys}
    @property
    def summary(self) -> pd.DataFrame:
        rows = [{"fold": f.fold, **f.metrics} for f in self.folds]
        return pd.DataFrame(rows).set_index("fold")

# Finance metrics (minimal; plug real ones if available)
def _sharpe(res) -> float:
    eq = getattr(res, "equity_curve", None)
    if eq is None or len(eq) < 2: return 0.0
    rets = eq.pct_change().dropna()
    if rets.std(ddof=0) == 0: return 0.0
    return float(np.sqrt(252) * rets.mean() / (rets.std(ddof=0) + 1e-12))

def _max_dd(res) -> float:
    eq = getattr(res, "equity_curve", None)
    if eq is None or len(eq) < 2: return 0.0
    roll_max = eq.cummax()
    dd = (eq / roll_max) - 1.0
    return float(dd.min())

WF_METRICS = {"sharpe": _sharpe, "max_dd": _max_dd}

class WalkForwardAdapter:
    def __init__(self, backtest_engine: Optional[BacktestEngine] = None, metrics=WF_METRICS):
        self.engine = backtest_engine or BacktestEngine()
        self.metrics = metrics

    def run(self, data: pd.DataFrame, strategy, n_splits=5, test_size=63, gap: int = 1) -> WFResults:
        results = WFResults()
        tscv = TimeSeriesSplit(n_splits=n_splits, test_size=test_size, gap=gap)

        for fold, (train_idx, test_idx) in enumerate(tscv.split(data)):
            train_df = data.iloc[train_idx]
            test_df  = data.iloc[test_idx]

            if hasattr(strategy, "fit"):
                strategy.fit(train_df)

            fold_bt = self.engine.run(data=test_df, strategy=strategy)

            fold_metrics = {name: fn(fold_bt) for name, fn in self.metrics.items()}
            fold_metrics["turnover"] = self._calc_turnover(getattr(fold_bt, "positions", None))
            results.folds.append(FoldReport(fold=fold, metrics=fold_metrics))

        return results

    @staticmethod
    def _calc_turnover(positions: Optional[pd.Series]) -> float:
        if positions is None or len(positions) < 2:
            return 0.0
        return float(np.abs(positions.diff().fillna(0)).sum() / len(positions))

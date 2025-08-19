import pandas as pd
from dataclasses import dataclass, field
from typing import Callable, Dict, Any, List
from sklearn.model_selection import TimeSeriesSplit

from .risk_execution_adapter import RiskExecutionAdapter
from ..utils.metrics import sharpe, max_drawdown, win_rate, turnover

@dataclass
class FoldResult:
    metrics: Dict[str, float]

@dataclass
class WFReport:
    strategy: str
    folds: List[FoldResult] = field(default_factory=list)

    def aggregate(self) -> Dict[str, float]:
        if not self.folds: return {"sharpe":0.0,"max_dd":0.0,"win_rate":0.0,"turnover":0.0}
        agg = {}
        for k in self.folds[0].metrics.keys():
            vals = [f.metrics[k] for f in self.folds]
            if k == "max_dd":
                agg[k] = float(pd.Series(vals).mean())
            else:
                agg[k] = float(pd.Series(vals).mean())
        return agg

class WalkForwardEngine:
    def __init__(self, n_splits: int = 5, test_size: int = 63):
        self.n_splits = n_splits; self.test_size = test_size

    def run(self, strategy, data: pd.DataFrame) -> WFReport:
        tscv = TimeSeriesSplit(n_splits=self.n_splits, test_size=self.test_size)
        report = WFReport(getattr(strategy, "name", strategy.__class__.__name__))

        # Single-asset path; multi-asset support can be plugged in by passing dict to RiskExecutionAdapter
        adapter = RiskExecutionAdapter(primary_symbol="ASSET")

        for fold, (tr_idx, te_idx) in enumerate(tscv.split(data)):
            df_train = data.iloc[tr_idx]
            df_test  = data.iloc[te_idx]
            if hasattr(strategy, "fit"):
                try:
                    strategy.fit(df_train)
                except Exception:
                    # keep going even if fit isn't implemented
                    pass
            res = adapter.run(df_test, strategy)
            eq = getattr(res, "equity_curve", (1 + df_test["close"].pct_change().fillna(0)).cumprod())
            pos = getattr(res, "positions", None)
            r = eq.pct_change().fillna(0.0)

            fold_metrics = {
                "sharpe": sharpe(eq),
                "max_dd": max_drawdown(eq),
                "win_rate": win_rate(r),
                "turnover": turnover(pos) if pos is not None else 0.0
            }
            report.folds.append(FoldResult(metrics=fold_metrics))
        return report

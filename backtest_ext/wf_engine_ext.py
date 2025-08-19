import pandas as pd
from dataclasses import dataclass, field
from typing import Dict, List
from sklearn.model_selection import TimeSeriesSplit

@dataclass
class FoldResultExt:
    metrics: Dict[str, float]

@dataclass
class WFReportExt:
    strategy: str
    folds: List[FoldResultExt] = field(default_factory=list)
    def aggregate(self) -> Dict[str, float]:
        if not self.folds:
            return {"sharpe":0.0, "max_dd":0.0, "win_rate":0.0, "turnover":0.0}
        first = self.folds[0].metrics.keys()
        out = {k: float(pd.Series([f.metrics[k] for f in self.folds]).mean()) for k in first}
        return out

# Minimal, non-invasive WF engine (does not depend on project BacktestEngine)
class WalkForwardEngineExt:
    def __init__(self, n_splits=5, test_size=63):
        self.n_splits = n_splits; self.test_size = test_size
    def run(self, strategy, data: pd.DataFrame) -> WFReportExt:
        from src.utils.metrics import sharpe, max_drawdown, win_rate  # try project metrics
        try:
            from src.utils.metrics import turnover
        except Exception:
            def turnover(_): return 0.0

        tscv = TimeSeriesSplit(n_splits=self.n_splits, test_size=self.test_size)
        rep = WFReportExt(getattr(strategy, "name", strategy.__class__.__name__))
        for tr, te in tscv.split(data):
            df_tr, df_te = data.iloc[tr], data.iloc[te]
            if hasattr(strategy, "fit"):
                try: strategy.fit(df_tr)
                except Exception: pass
            # Simple equity (proof-of-life). Projects can plug their own adapter.
            proba = strategy.predict_proba(df_te)
            sig = (proba>0.55).astype(int) - (proba<0.45).astype(int)
            ret = df_te["close"].pct_change().shift(-1).fillna(0.0)
            eq = (1 + (sig*0.1*ret)).cumprod()  # 10% weight proxy
            m = {"sharpe": sharpe(eq), "max_dd": max_drawdown(eq), "win_rate": win_rate(ret), "turnover": 0.0}
            rep.folds.append(FoldResultExt(metrics=m))
        return rep

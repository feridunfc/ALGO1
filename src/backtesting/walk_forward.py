from __future__ import annotations
import numpy as np
import pandas as pd
from dataclasses import dataclass
from typing import Callable, Dict, Any, List, Optional, Tuple
from sklearn.model_selection import TimeSeriesSplit

@dataclass
class FoldResult:
    fold: int
    start: str
    end: str
    sharpe: float
    sortino: float
    maxdd: float
    calmar: float
    ann_return: float
    ann_vol: float
    trades: int

def _to_returns(prices: pd.Series) -> pd.Series:
    return np.log(prices / prices.shift(1)).fillna(0.0)

def _equity_from_signals(prices: pd.Series, signals: pd.Series, tc_bps: float = 0.0) -> pd.Series:
    # signals in {-1,0,+1}; apply T+1 execution at open (approx: shift position by 1)
    pos = signals.shift(1).fillna(0.0)
    rets = _to_returns(prices) * pos
    # simple transaction cost on position change
    tc = (pos.diff().abs().fillna(0.0)) * (tc_bps / 10000.0)
    rets = rets - tc
    equity = (1.0 + rets).cumprod()
    return equity

def _metrics_from_equity(eq: pd.Series) -> Dict[str, float]:
    rets = eq.pct_change().dropna()
    if rets.empty:
        return dict(sharpe=0.0, sortino=0.0, maxdd=0.0, calmar=0.0, ann_return=0.0, ann_vol=0.0, trades=0)
    mu = rets.mean() * 252
    vol = rets.std(ddof=0) * np.sqrt(252)
    sharpe = (mu / vol) if vol > 0 else 0.0
    neg = rets[rets < 0]
    dvol = neg.std(ddof=0) * np.sqrt(252)
    sortino = (mu / dvol) if dvol > 0 else 0.0
    peak = eq.cummax()
    dd = (peak - eq) / peak
    maxdd = dd.max() if len(dd) else 0.0
    calmar = (mu / maxdd) if maxdd > 1e-9 else 0.0
    return dict(sharpe=float(sharpe), sortino=float(sortino), maxdd=float(maxdd),
                calmar=float(calmar), ann_return=float(mu), ann_vol=float(vol), trades=int((pos_changes:=0)))

class WalkForwardRunner:
    """Walk-forward analizi: strategy.fit(train) → predict(test) → metrics.
    Strategy API:
      - train(X_train: DataFrame, y_train: Series/None) -> None
      - predict_signals(X_test: DataFrame) -> Series in {-1,0,+1}
    """
    def __init__(self, n_splits: int = 5, test_size: Optional[int] = None, tc_bps: float = 0.0):
        self.n_splits = n_splits
        self.test_size = test_size
        self.tc_bps = tc_bps

    def run(self,
            features: pd.DataFrame,
            prices: pd.Series,
            strategy_factory: Callable[..., Any],
            strategy_params: Dict[str, Any]) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        tscv = TimeSeriesSplit(n_splits=self.n_splits, test_size=self.test_size)
        fold_rows: List[Dict[str, Any]] = []
        eq_curves = {}
        for fold, (tr_idx, te_idx) in enumerate(tscv.split(features), start=1):
            X_tr, X_te = features.iloc[tr_idx], features.iloc[te_idx]
            p_tr, p_te = prices.iloc[te_idx[0]:te_idx[-1]+1], prices.iloc[te_idx]  # price segment aligned
            strat = strategy_factory(**strategy_params)
            # Some strategies may expect y, we pass None by default
            if hasattr(strat, "train"):
                try:
                    strat.train(X_tr, None)
                except TypeError:
                    strat.train(X_tr)
            sig = strat.predict_signals(X_te)
            sig = sig.reindex(p_te.index).fillna(0.0)
            eq = _equity_from_signals(p_te, sig, tc_bps=self.tc_bps)
            eq_curves[f"fold_{fold}"] = eq
            m = _metrics_from_equity(eq)
            fold_rows.append(dict(fold=fold, start=str(p_te.index.min()), end=str(p_te.index.max()), **m))
        df = pd.DataFrame(fold_rows)
        summary = dict(mean_sharpe=float(df['sharpe'].mean() if not df.empty else 0.0),
                       median_sharpe=float(df['sharpe'].median() if not df.empty else 0.0),
                       folds=len(df))
        return df, summary

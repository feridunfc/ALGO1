import numpy as np
import pandas as pd

def _to_returns(equity_or_returns: pd.Series) -> pd.Series:
    s = equity_or_returns
    if s is None or len(s) == 0:
        return pd.Series([], dtype=float)
    if (s <= 0).any() or s.max() < 5:
        # probably returns already
        return s.fillna(0.0)
    # equity -> returns
    r = s.pct_change().fillna(0.0)
    return r

def sharpe(equity_or_returns: pd.Series, rf: float = 0.0, annualization: int = 252) -> float:
    r = _to_returns(equity_or_returns)
    if len(r) < 2: return 0.0
    ex = r - rf/annualization
    sd = ex.std(ddof=0)
    if sd <= 1e-12: return 0.0
    return float((ex.mean() / sd) * np.sqrt(annualization))

def max_drawdown(equity_curve: pd.Series) -> float:
    if equity_curve is None or len(equity_curve) == 0:
        return 0.0
    cummax = equity_curve.cummax()
    dd = (equity_curve / cummax) - 1.0
    return float(dd.min())

def win_rate(returns: pd.Series) -> float:
    r = _to_returns(returns)
    if len(r) == 0: return 0.0
    wins = (r > 0).sum()
    return float(wins) / len(r)

def turnover(positions_df: pd.DataFrame) -> float:
    if positions_df is None or positions_df.empty:
        return 0.0
    # daily turnover ~ sum abs(day-to-day weight change)
    dw = positions_df.diff().abs().sum(axis=1).fillna(0.0)
    return float(dw.mean())

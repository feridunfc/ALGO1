from __future__ import annotations
import numpy as np, pandas as pd

def sharpe(returns: pd.Series, rf=0.0, period=252):
    r = returns.dropna()
    if r.std(ddof=0) == 0: return 0.0
    return (r.mean() - rf/period) / (r.std(ddof=0) + 1e-12) * np.sqrt(period)

def sortino(returns: pd.Series, rf=0.0, period=252):
    r = returns.dropna()
    downside = r[r < 0]
    dd = downside.std(ddof=0)
    if dd == 0: return 0.0
    return (r.mean() - rf/period) / (dd + 1e-12) * np.sqrt(period)

def max_drawdown(equity: pd.Series):
    roll = equity.cummax()
    dd = equity/roll - 1.0
    return dd.min()

def compute_metrics(equity: pd.Series):
    ret = equity.pct_change().fillna(0.0)
    return {
        "total_return": float(equity.iloc[-1] / equity.iloc[0] - 1.0),
        "sharpe": float(sharpe(ret)),
        "sortino": float(sortino(ret)),
        "maxdd": float(max_drawdown(equity)),
    }

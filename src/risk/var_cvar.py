
from __future__ import annotations
import numpy as np
import pandas as pd

def historical_var(returns: pd.Series, alpha: float = 0.95) -> float:
    r = returns.dropna().sort_values()
    if len(r) == 0:
        return 0.0
    idx = int((1-alpha) * len(r))
    return float(-r.iloc[idx])

def historical_cvar(returns: pd.Series, alpha: float = 0.95) -> float:
    r = returns.dropna().sort_values()
    if len(r) == 0:
        return 0.0
    cutoff = int((1-alpha) * len(r))
    tail = r.iloc[:max(cutoff,1)]
    return float(-tail.mean()) if len(tail)>0 else 0.0

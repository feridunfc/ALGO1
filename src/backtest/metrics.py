
from __future__ import annotations
import pandas as pd
import numpy as np

def summarize(equity: pd.Series, trades: pd.DataFrame, freq: str = "D"):
    if len(equity) == 0:
        return {"total_return": 0.0, "sharpe": 0.0, "maxdd": 0.0}
    rets = equity.pct_change().fillna(0.0)
    mean = rets.mean(); std = rets.std()
    sharpe = (mean/std)*np.sqrt(252) if std>0 else 0.0
    total_ret = float(equity.iloc[-1]/equity.iloc[0]-1.0) if equity.iloc[0] != 0 else 0.0
    maxdd = float((equity / equity.cummax() - 1.0).min())
    return {"total_return": round(total_ret,4), "sharpe": round(sharpe,3), "maxdd": round(maxdd,4)}

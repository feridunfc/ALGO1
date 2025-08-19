
from __future__ import annotations
import pandas as pd

def drawdown_series(equity: pd.Series) -> pd.Series:
    return equity / equity.cummax() - 1.0

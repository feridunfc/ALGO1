
from __future__ import annotations
import pandas as pd
import numpy as np
from data_layer.indicators import sma, rsi

def ma_slope(series: pd.Series, window: int = 50) -> float:
    s = sma(series, window)
    if s.isna().iloc[-1] or len(s.dropna()) < 2:
        return 0.0
    # slope ~ last diff
    return float(s.iloc[-1] - s.iloc[-2])

def detect_regime(df: pd.DataFrame) -> str:
    """Return one of: BULL, BEAR, SIDEWAYS based on MA cross & slope & RSI."""
    if len(df) < 200:
        return "UNKNOWN"
    ma50 = sma(df["close"], 50)
    ma200 = sma(df["close"], 200)
    last = len(df) - 1
    if pd.isna(ma50.iloc[last]) or pd.isna(ma200.iloc[last]):
        return "UNKNOWN"
    slope50 = ma50.diff().iloc[last]
    # Simple logic
    if ma50.iloc[last] > ma200.iloc[last] and slope50 > 0:
        return "BULL"
    if ma50.iloc[last] < ma200.iloc[last] and slope50 < 0:
        return "BEAR"
    return "SIDEWAYS"

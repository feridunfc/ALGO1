
from __future__ import annotations
import pandas as pd
import numpy as np
from schemas.signal import Signal
from data_layer.indicators import rsi

def bollinger_bands(close: pd.Series, window: int = 20, k: float = 2.0):
    ma = close.rolling(window, min_periods=window).mean()
    sd = close.rolling(window, min_periods=window).std()
    upper = ma + k*sd
    lower = ma - k*sd
    return ma, upper, lower

def signal_bb_meanrev(df: pd.DataFrame, window: int = 20, k: float = 2.0, symbol: str = "UNKNOWN"):
    if len(df) < window:
        return None
    ma, upper, lower = bollinger_bands(df["close"], window, k)
    last = len(df) - 1
    r = rsi(df["close"], 14).iloc[last]
    c = df["close"].iloc[last]
    # mean reversion: buy if below lower and rsi < 30; sell if above upper and rsi > 70
    if not (np.isnan(upper.iloc[last]) or np.isnan(lower.iloc[last]) or np.isnan(r)):
        if c < lower.iloc[last] and r < 30:
            return Signal(symbol=symbol, side="BUY", strength=0.5, ttl_sec=60, model="rules.bb_meanrev")
        if c > upper.iloc[last] and r > 70:
            return Signal(symbol=symbol, side="SELL", strength=0.5, ttl_sec=60, model="rules.bb_meanrev")
    return None


from __future__ import annotations
import pandas as pd
from data_layer.indicators import sma
from schemas.signal import Signal

def signal_ma_crossover(df: pd.DataFrame, fast: int = 20, slow: int = 50, symbol: str = "UNKNOWN"):
    if len(df) < max(fast, slow) + 1:
        return None
    f = sma(df["close"], fast)
    s = sma(df["close"], slow)
    # cross detection (last two points)
    prev = len(df) - 2
    last = len(df) - 1
    if f.iloc[prev] <= s.iloc[prev] and f.iloc[last] > s.iloc[last]:
        return Signal(symbol=symbol, side="BUY", strength=0.6, ttl_sec=60, model="rules.ma_cross")
    if f.iloc[prev] >= s.iloc[prev] and f.iloc[last] < s.iloc[last]:
        return Signal(symbol=symbol, side="SELL", strength=0.6, ttl_sec=60, model="rules.ma_cross")
    return None

import pandas as pd
from ..base import Strategy

class Breakout(Strategy):
    name = "rb_breakout"
    def __init__(self, lookback=20):
        self.lookback=lookback
    def predict_proba(self, df: pd.DataFrame) -> pd.Series:
        hi = df["high"].rolling(self.lookback, min_periods=self.lookback).max()
        lo = df["low"].rolling(self.lookback, min_periods=self.lookback).min()
        mid = (hi + lo)/2.0
        signal = (df["close"] > mid).astype(float)
        p = 0.5 + (signal - 0.5)*0.5
        return p.fillna(0.5)

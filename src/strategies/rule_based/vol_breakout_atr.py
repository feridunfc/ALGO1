import pandas as pd
from ..base import Strategy
from ...risk.position_sizer import atr

class VolatilityBreakoutATR(Strategy):
    name = "rb_vol_breakout_atr"
    def __init__(self, n=14, k=1.0):
        self.n=n; self.k=k
    def predict_proba(self, df):
        a = atr(df["high"], df["low"], df["close"], n=self.n)
        trigger = df["open"] + self.k * a
        p = (df["close"] > trigger).astype(float)*0.25 + (df["close"]<=trigger).astype(float)*0.75
        # invert so that close>trigger => bullish (0.75)
        p[df["close"] > trigger] = 0.75
        p[df["close"] <= trigger] = 0.25
        return p.fillna(0.5).clip(0,1)

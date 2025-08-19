import pandas as pd
from ..base import Strategy

class DonchianBreakout(Strategy):
    name = "rb_donchian_breakout"
    def __init__(self, n=20):
        self.n=n
    def predict_proba(self, df):
        hi = df["high"].rolling(self.n, min_periods=self.n).max()
        lo = df["low"].rolling(self.n, min_periods=self.n).min()
        p = (df["close"] - lo) / (hi - lo + 1e-12)
        return p.fillna(0.5).clip(0,1)

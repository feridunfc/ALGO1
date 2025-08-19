import pandas as pd
from ..base import Strategy

class StochasticOsc(Strategy):
    name = "rb_stochastic"
    def __init__(self, n=14):
        self.n=n
    def predict_proba(self, df):
        hi = df["high"].rolling(self.n, min_periods=self.n).max()
        lo = df["low"].rolling(self.n, min_periods=self.n).min()
        k = (df["close"] - lo) / (hi - lo + 1e-12)
        return k.fillna(0.5).clip(0,1)

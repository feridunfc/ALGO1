import pandas as pd
from ..base import Strategy
from ..features import rsi

class RSIThreshold(Strategy):
    name = "rb_rsi_threshold"
    def __init__(self, n=14, lo=30, hi=70):
        self.n=n; self.lo=lo; self.hi=hi
    def predict_proba(self, df):
        rs = rsi(df["close"], self.n)
        p = (rs - 50)/100 + 0.5
        return p.fillna(0.5).clip(0.0,1.0)

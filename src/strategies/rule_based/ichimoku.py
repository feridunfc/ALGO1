import pandas as pd
from ..base import Strategy

class IchimokuTrend(Strategy):
    name = "rb_ichimoku"
    def __init__(self, conv=9, base=26):
        self.conv=conv; self.base=base
    def predict_proba(self, df):
        conv = (df["high"].rolling(self.conv).max() + df["low"].rolling(self.conv).min())/2.0
        base = (df["high"].rolling(self.base).max() + df["low"].rolling(self.base).min())/2.0
        p = (conv > base).astype(float)*0.25 + 0.5
        p[conv>base] = 0.75
        p[conv<=base] = 0.25
        return p.fillna(0.5).clip(0,1)

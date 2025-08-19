import pandas as pd
from ..base import Strategy

class BollingerReversion(Strategy):
    name = "rb_bollinger_reversion"
    def __init__(self, n=20, k=2):
        self.n=n; self.k=k
    def predict_proba(self, df):
        ma = df["close"].rolling(self.n, min_periods=self.n).mean()
        sd = df["close"].rolling(self.n, min_periods=self.n).std(ddof=0)
        up = ma + self.k*sd; dn = ma - self.k*sd
        p = df["close"].copy()*0 + 0.5
        p[df["close"]<dn] = 0.75  # mean reversion long
        p[df["close"]>up] = 0.25  # mean reversion short
        return p.fillna(0.5).clip(0,1)

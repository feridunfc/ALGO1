import pandas as pd, numpy as np
from ..base import Strategy

class ADXTrend(Strategy):
    name = "rb_adx_trend"
    def __init__(self, n=14):
        self.n=n
    def predict_proba(self, df):
        # Simplified ADX proxy: directional movement via rolling trend strength
        ret = np.sign(df["close"].diff()).rolling(self.n, min_periods=self.n).mean()
        p = 0.5 + 0.5*ret
        return p.fillna(0.5).clip(0,1)

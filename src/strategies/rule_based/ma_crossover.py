import pandas as pd
from ..base import Strategy

class MACrossover(Strategy):
    name = "rb_ma_crossover"
    def __init__(self, fast=20, slow=50):
        self.fast=fast; self.slow=slow
    def predict_proba(self, df: pd.DataFrame) -> pd.Series:
        ma_f = df["close"].rolling(self.fast, min_periods=self.fast).mean()
        ma_s = df["close"].rolling(self.slow, min_periods=self.slow).mean()
        signal = (ma_f > ma_s).astype(float)
        p = 0.5 + (signal - 0.5)*0.5
        return p.fillna(0.5)

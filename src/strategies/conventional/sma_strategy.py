import pandas as pd
from ..base_strategy import BaseStrategy

class SMACrossoverStrategy(BaseStrategy):
    def __init__(self, params=None):
        super().__init__("sma_crossover", params)
        self.short = int(self.params.get("short_window", 20))
        self.long = int(self.params.get("long_window", 50))

    def predict(self, df: pd.DataFrame) -> pd.Series:
        c = df["close"].astype(float)
        ma_s = c.rolling(self.short, min_periods=1).mean()
        ma_l = c.rolling(self.long, min_periods=1).mean()
        raw = (ma_s > ma_l).astype(int) - (ma_s < ma_l).astype(int)
        sig = raw.shift(1).fillna(0.0)
        sig.name = "signal"
        return sig

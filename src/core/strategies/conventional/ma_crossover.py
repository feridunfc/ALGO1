from __future__ import annotations
import numpy as np, pandas as pd

class MovingAverageCrossover:
    name = "ma_crossover"
    def __init__(self, ma_fast: int = 20, ma_slow: int = 50):
        self.ma_fast = int(ma_fast); self.ma_slow = int(ma_slow)
    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        c = df["close"]
        f = c.rolling(self.ma_fast).mean()
        s = c.rolling(self.ma_slow).mean()
        raw = (f > s).astype(float) * 2 - 1  # 1 or -1
        return raw.fillna(0.0).rename("signal")

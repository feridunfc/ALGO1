from __future__ import annotations
import pandas as pd

class MarketRegimeDetector:
    def __init__(self, vol_window: int = 21, trend_window: int = 63):
        self.vol_w = vol_window
        self.trend_w = trend_window

    def detect(self, close: pd.Series) -> str:
        ret = close.pct_change()
        vol = ret.rolling(self.vol_w, min_periods=5).std()
        mom = close.pct_change(self.trend_w)
        v = vol.iloc[-1]
        m = mom.iloc[-1]
        if pd.isna(v) or pd.isna(m):
            return "unknown"
        if v > ret.std()*1.2:
            return "high_vol"
        if abs(m) > 0.1 and v < ret.std()*1.0:
            return "trending"
        return "low_vol"

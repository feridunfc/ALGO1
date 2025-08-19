
from __future__ import annotations
import numpy as np
import pandas as pd
from typing import Optional
from .enhanced_risk_engine import MarketRegime

class MarketRegimeDetector:
    """Very small heuristic regime detector.
    - Trend via 50/200 SMA crossover
    - Volatility via 20d std of returns
    """
    def __init__(self, vol_thresh_low: float = 0.012, vol_thresh_high: float = 0.03):
        self.vol_low = vol_thresh_low
        self.vol_high = vol_thresh_high

    def detect(self, features: pd.DataFrame) -> MarketRegime:
        if features is None or len(features) < 210:
            return MarketRegime.SIDEWAYS
        close = features["close"]
        sma50 = close.rolling(50).mean()
        sma200 = close.rolling(200).mean()
        ret = close.pct_change().dropna()
        vol = ret.rolling(20).std().iloc[-1]

        if vol is None or np.isnan(vol):
            return MarketRegime.SIDEWAYS

        if sma50.iloc[-1] > sma200.iloc[-1]:
            # uptrend
            if vol < self.vol_low:
                return MarketRegime.BULL
            elif vol > self.vol_high:
                return MarketRegime.RECOVERY  # volatile up
            else:
                return MarketRegime.BULL
        else:
            # downtrend
            if vol > self.vol_high:
                return MarketRegime.CRISIS
            else:
                return MarketRegime.BEAR

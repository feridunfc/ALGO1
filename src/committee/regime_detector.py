from __future__ import annotations
import pandas as pd
from dataclasses import dataclass

@dataclass
class RegimeConfig:
    vol_lookback: int = 63
    trend_lookback: int = 63
    vol_high: float = 0.02  # günlük std eşiği

class MarketRegimeDetector:
    """Benchmark kapanış serisinden trend+vol’a göre rejim tespiti."""
    def __init__(self, benchmark_close: pd.Series, cfg: RegimeConfig | None = None):
        self.close = benchmark_close.dropna()
        self.cfg = cfg or RegimeConfig()

    def current(self) -> str:
        ret = self.close.pct_change().dropna()
        vol = ret.rolling(self.cfg.vol_lookback,
                          min_periods=self.cfg.vol_lookback//2).std().iloc[-1]
        trend = (self.close.iloc[-1] /
                 self.close.rolling(self.cfg.trend_lookback,
                                    min_periods=self.cfg.trend_lookback//2).mean().iloc[-1]) - 1
        if vol >= self.cfg.vol_high and trend < 0:
            return "crisis"
        if trend > 0:
            return "bullish" if vol < self.cfg.vol_high else "volatile_up"
        return "sideways"


from __future__ import annotations
from typing import Dict, Any, Optional
from collections import defaultdict
import pandas as pd

def signal_ma_crossover(prices: list[float], fast: int, slow: int) -> int:
    if len(prices) < max(fast, slow):
        return 0
    s = pd.Series(prices)
    fma = s.rolling(fast, min_periods=1).mean().iloc[-1]
    sma = s.rolling(slow, min_periods=1).mean().iloc[-1]
    return 1 if fma > sma else 0

class CorePipeline:
    def __init__(self, bus=None, feature_spec: Optional[Dict[str, Any]] = None, max_history: int = 500, strategy_params: Optional[Dict[str, Any]] = None):
        self.bus = bus
        self.feature_spec = feature_spec or {}
        self.max_history = max_history
        self.params = strategy_params or {"ma_fast": 10, "ma_slow": 30}
        self.hist = defaultdict(list)

    def on_bar(self, sym: str, close_price: float) -> int:
        self.hist[sym].append(close_price)
        if len(self.hist[sym]) > self.max_history:
            self.hist[sym] = self.hist[sym][-self.max_history:]
        mf = int(self.params.get("ma_fast", 10))
        ms = int(self.params.get("ma_slow", 30))
        return signal_ma_crossover(self.hist[sym], mf, ms)

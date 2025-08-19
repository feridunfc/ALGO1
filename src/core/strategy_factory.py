
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any
import numpy as np
import pandas as pd

class BaseStrategy:
    name: str = "base"
    def generate_signal(self, features: pd.DataFrame) -> float:
        raise NotImplementedError

class MomentumStrategy(BaseStrategy):
    name = "momentum_v1"
    def __init__(self, lookback: int = 20):
        self.lookback = lookback

    def generate_signal(self, features: pd.DataFrame) -> float:
        close = features["close"]
        if len(close) < self.lookback + 1:
            return 0.0
        ret = close.iloc[-1] / close.iloc[-self.lookback] - 1.0
        # scale to [-1,1]
        return float(np.tanh(ret * 5))

class RSIStrategy(BaseStrategy):
    name = "rsi_contra_v1"
    def __init__(self, lower: float = 30.0, upper: float = 70.0):
        self.lower = lower
        self.upper = upper

    def generate_signal(self, features: pd.DataFrame) -> float:
        # naive RSI using rolling
        delta = features["close"].diff()
        up = delta.clip(lower=0).rolling(14).mean()
        down = (-delta.clip(upper=0)).rolling(14).mean()
        rs = (up / (down.replace(0, np.nan))).fillna(1.0)
        rsi = 100 - (100 / (1 + rs))
        val = rsi.iloc[-1]
        if val < self.lower:
            return +0.6  # buy bias
        if val > self.upper:
            return -0.6  # sell bias
        return 0.0

class StrategyFactory:
    def __init__(self, config):
        self.config = config

    def load_all(self) -> Dict[str, BaseStrategy]:
        # In real system, dynamically discover & instantiate registry entries
        return {
            MomentumStrategy.name: MomentumStrategy(lookback=20),
            RSIStrategy.name: RSIStrategy(lower=30, upper=70),
        }

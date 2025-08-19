import numpy as np, pandas as pd
from typing import Optional
import warnings

class RiskManager:
    def __init__(self, target_volatility: float = 0.2, kelly_fraction: float = 0.5, max_leverage: float = 2.0):
        self.target_vol = target_volatility
        self.kelly_frac = kelly_fraction
        self.max_leverage = max_leverage

    def calculate_position_size(self, symbol: str, signal_confidence: float, volatility: float, atr: float, portfolio_value: float) -> float:
        vol_scale = self.target_vol / (volatility + 1e-9)
        kelly_size = signal_confidence * vol_scale
        fractional_kelly = self.kelly_frac * kelly_size
        max_size = min(fractional_kelly, self.max_leverage)
        return float(max(0.0, min(1.0, max_size)))

    def calculate_stop_loss(self, entry_price: float, atr: float, volatility: float, multiplier: float = 2.0) -> float:
        stop_distance = max(atr, volatility * entry_price)
        return float(entry_price - (multiplier * stop_distance))

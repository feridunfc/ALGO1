from __future__ import annotations
from dataclasses import dataclass
import numpy as np, pandas as pd

@dataclass
class RiskParams:
    stop_loss: float = 0.0
    take_profit: float = 0.0
    kelly_fraction: float = 0.0
    vol_target: float = 0.0  # annualized target, 0 disables

class RiskEngine:
    def __init__(self, params: RiskParams):
        self.p = params

    def position_size(self, ret_vol: float, edge: float = 0.0):
        # Kelly
        k = max(0.0, min(1.0, self.p.kelly_fraction))
        kelly_size = k

        # Vol targeting -> scale so that daily vol ~ vol_target/√period
        vol_size = 1.0
        if self.p.vol_target and ret_vol > 0:
            target_daily = self.p.vol_target / np.sqrt(252.0)
            vol_size = float(target_daily / (ret_vol + 1e-12))

        size = kelly_size if k > 0 else 1.0
        size *= vol_size
        return max(0.0, min(1.0, size))

    def apply_stops(self, price_now: float, entry: float):
        sl_hit = False; tp_hit = False
        if self.p.stop_loss > 0 and price_now <= entry * (1 - self.p.stop_loss):
            sl_hit = True
        if self.p.take_profit > 0 and price_now >= entry * (1 + self.p.take_profit):
            tp_hit = True
        return sl_hit, tp_hit

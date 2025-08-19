
import numpy as np

class AdvancedRiskManager:
    def __init__(self, target_vol: float = 0.15, max_position_weight_pct: float = 0.10):
        self.target_vol = target_vol  # annual target
        self.max_w = max_position_weight_pct

    def calculate_position(self, symbol_vol_daily: float, portfolio_value: float) -> float:
        if symbol_vol_daily <= 0 or np.isnan(symbol_vol_daily):
            return 0.0
        target_daily = self.target_vol / np.sqrt(252.0)
        pos_value = (target_daily / symbol_vol_daily) * portfolio_value
        return min(pos_value, portfolio_value * self.max_w)

    def cap_by_weight(self, position_value: float, portfolio_value: float) -> float:
        return min(position_value, portfolio_value * self.max_w)

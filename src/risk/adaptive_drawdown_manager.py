
import numpy as np

class AdaptiveDrawdownManager:
    def __init__(self, base_threshold=0.20):
        self.peak_equity = -np.inf
        self.drawdown_threshold = base_threshold

    def update_threshold(self, volatility: float):
        # shrink threshold as vol rises; floor at 5%
        self.drawdown_threshold = max(0.05, 0.20 - float(volatility) * 2.0)

    def check_drawdown(self, current_equity: float) -> bool:
        self.peak_equity = max(self.peak_equity, current_equity)
        if self.peak_equity <= 0 or not np.isfinite(self.peak_equity):
            return False
        current_dd = (self.peak_equity - current_equity) / self.peak_equity
        return current_dd > self.drawdown_threshold

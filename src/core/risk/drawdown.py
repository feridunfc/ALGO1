import numpy as np
class AdaptiveDrawdownGuard:
    def __init__(self, base=0.20): self.peak=-np.inf; self.th=base
    def update_threshold(self, realized_vol: float): self.th = max(0.05, 0.20 - 2.0*realized_vol)
    def breach(self, current_equity: float)->bool:
        self.peak = max(self.peak, current_equity)
        if self.peak<=0: return False
        dd = 1.0 - (current_equity/self.peak)
        return dd > self.th

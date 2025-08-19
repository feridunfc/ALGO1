import numpy as np

class RiskManagerEngine:
    def __init__(self, target_vol_annual=0.15, max_dd=0.25):
        self.target_vol_annual = float(target_vol_annual)
        self.max_dd = float(max_dd)
        self.returns = []
        self.equity = 1.0
        self.peak = 1.0

    def update_equity(self, equity: float):
        self.equity = equity
        if equity > self.peak:
            self.peak = equity

    def realized_vol(self, window=63):
        # daily vol
        if len(self.returns) < 2:
            return 0.0
        arr = np.array(self.returns[-window:], dtype=float)
        return float(np.nanstd(arr, ddof=1))

    def dd_exceeded(self) -> bool:
        if self.equity <= 0:
            return True
        dd = 1.0 - self.equity/self.peak
        return dd >= self.max_dd

    def decide_weight(self, raw_direction: int, daily_ret: float) -> float:
        # update realized returns
        self.returns.append(float(daily_ret))

        if self.dd_exceeded():
            return 0.0

        # simple vol targeting
        daily_target_vol = self.target_vol_annual / np.sqrt(252.0)
        rv = self.realized_vol()
        if rv <= 1e-8:
            scale = 0.0
        else:
            scale = daily_target_vol / rv
        scale = float(np.clip(scale, 0.0, 3.0))  # cap leverage
        return float(np.clip(raw_direction * scale, -1.0, 1.0))

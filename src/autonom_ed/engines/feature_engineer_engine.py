from collections import deque
import numpy as np

class FeatureEngineerEngine:
    def __init__(self, ma_fast=20, ma_slow=50):
        self.ma_fast = ma_fast
        self.ma_slow = ma_slow
        self.window_fast = deque(maxlen=ma_fast)
        self.window_slow = deque(maxlen=ma_slow)
        self.last_price = None
        self.last_return = 0.0

    def update_and_compute(self, price: float) -> dict:
        # Update rolling windows
        self.window_fast.append(price)
        self.window_slow.append(price)

        sma_fast = np.mean(self.window_fast) if len(self.window_fast) == self.window_fast.maxlen else np.nan
        sma_slow = np.mean(self.window_slow) if len(self.window_slow) == self.window_slow.maxlen else np.nan

        ret = 0.0 if self.last_price is None else (price / self.last_price - 1.0)
        self.last_price = price
        self.last_return = ret

        return {
            "close": price,
            "ret1": ret,
            "sma_fast": sma_fast,
            "sma_slow": sma_slow,
        }

import numpy as np
import pandas as pd

TRADING_DAYS = 252

class VolTargetSizer:
    def __init__(self, target_vol: float = 0.15, lookback: int = 20):
        self.target = target_vol
        self.lookback = lookback

    def scale(self, ret: pd.Series, base_pos: pd.Series) -> pd.Series:
        # realized vol (daily) -> annualize
        rolling_vol = ret.rolling(self.lookback).std(ddof=0) * np.sqrt(TRADING_DAYS)
        scale = (self.target / rolling_vol).clip(upper=5.0).fillna(0.0)
        return (base_pos * scale).clip(-2, 2)  # cap leverage

class MaxDrawdownStop:
    def __init__(self, max_dd: float = 0.3):
        self.max_dd = max_dd

    def apply(self, port_ret: pd.Series) -> pd.Series:
        equity = (1.0 + port_ret).cumprod()
        peak = equity.cummax()
        dd = equity/peak - 1.0
        stopped = dd < -abs(self.max_dd)
        # zero out returns after stop is hit
        if stopped.any():
            first_idx = stopped.idxmax() if stopped.any() else None
            if first_idx is not None and stopped.loc[first_idx]:
                # from first_idx onwards, returns = 0
                port_ret.loc[first_idx:] = 0.0
        return port_ret

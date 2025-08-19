import numpy as np, pandas as pd
from dataclasses import dataclass

@dataclass
class PositionSizerParams:
    target_annual_vol: float = 0.20
    lookback_days: int = 30
    max_position_weight_pct: float = 0.10

class VolTargetSizer:
    def __init__(self, params: PositionSizerParams): self.p=params
    def size(self, df: pd.DataFrame, portfolio_value: float)->float:
        r = df['close'].pct_change().dropna()
        if len(r) < self.p.lookback_days: return 0.0
        realized = r.iloc[-self.p.lookback_days:].std()
        if realized <= 0: return 0.0
        target_daily = self.p.target_annual_vol/np.sqrt(252)
        pos_val = (target_daily/realized)*portfolio_value
        return float(min(pos_val, portfolio_value*self.p.max_position_weight_pct))

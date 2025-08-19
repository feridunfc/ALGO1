from __future__ import annotations
import numpy as np, pandas as pd

class VolatilityPositionSizer:
    def __init__(self, target_annual_vol: float=0.20, lookback_days: int=30):
        self.target_daily = float(target_annual_vol) / (252**0.5)
        self.lookback = int(lookback_days)

    def _realized_vol(self, series: pd.Series) -> float:
        r = series.pct_change().dropna().iloc[-self.lookback:]
        return float(r.std()) if len(r) else 0.0

    def _apply_limits(self, position_value: float, portfolio_value: float) -> float:
        max_pos = portfolio_value * 0.10
        return float(min(max(position_value, 0.0), max_pos))

    def calculate(self, price_series: pd.Series, portfolio_value: float) -> float:
        rv = self._realized_vol(price_series)
        if rv <= 0:
            return 0.0
        raw = (self.target_daily / rv) * portfolio_value
        return self._apply_limits(raw, portfolio_value)

class AdvancedPositionSizer(VolatilityPositionSizer):
    def __init__(self, target_annual_vol: float=0.20, lookback_days: int=30, regime_threshold: float=0.8):
        super().__init__(target_annual_vol, lookback_days)
        self.regime_threshold = float(regime_threshold)

    def calculate(self, price_series: pd.Series, portfolio_value: float) -> float:
        rv = self._realized_vol(price_series)
        if rv <= 0:
            return 0.0
        abs_ret = price_series.pct_change().abs().dropna()
        if len(abs_ret) < max(50, self.lookback):
            regime_adj = 1.0
        else:
            perc = abs_ret.rank(pct=True).iloc[-1]
            regime_adj = min(1.0, 1 - max(0.0, (perc - self.regime_threshold)) / (1 - self.regime_threshold + 1e-9))
        base = (self.target_daily / rv) * portfolio_value
        return self._apply_limits(base * regime_adj, portfolio_value)

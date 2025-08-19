"""Advanced risk utilities for AlgoSuite.
Features:
 - ATR-based stop calculation
 - position_size_percent_risk (percent risk per trade using ATR)
 - portfolio-level risk checks (max_exposure_pct, max_open_positions)
API (simple):
 from src.core.risk.advanced import AdvancedRisk
 risk = AdvancedRisk(cfg)
 units = risk.position_size_percent_risk(price, atr, capital, pct_risk=0.01)
 stop = risk.atr_stop_long(entry_price, atr, multiplier=3)
"""
import numpy as np
import pandas as pd

class AdvancedRisk:
    def __init__(self, cfg=None):
        cfg = cfg or {}
        self.cfg = {
            'pct_risk_per_trade': cfg.get('pct_risk_per_trade', 0.01),
            'max_exposure_pct': cfg.get('max_exposure_pct', 0.5),
            'max_open_positions': cfg.get('max_open_positions', 10),
            'min_units': cfg.get('min_units', 0.0),
        }

    @staticmethod
    def atr_from_df(df, lookback=14):
        """Calculate rolling ATR from df with columns high, low, close"""
        high = df['high']
        low = df['low']
        close = df['close']
        tr1 = (high - low).abs()
        tr2 = (high - close.shift()).abs()
        tr3 = (low - close.shift()).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(lookback, min_periods=1).mean()
        return atr

    def atr_stop_long(self, entry_price, atr, multiplier=3.0):
        return entry_price - multiplier * atr

    def atr_stop_short(self, entry_price, atr, multiplier=3.0):
        return entry_price + multiplier * atr

    def position_size_percent_risk(self, price, atr, capital, pct_risk=None, stop_multiplier=3.0):
        """Calculate units so that (entry_price - stop) * units = pct_risk * capital (approx)
        For long: stop = entry - stop_multiplier*atr => risk_per_unit = stop_multiplier*atr
        units = (pct_risk * capital) / (risk_per_unit)
        """
        if price is None or atr is None or price <=0 or atr<=0:
            return 0.0
        pct_risk = pct_risk if pct_risk is not None else self.cfg['pct_risk_per_trade']
        risk_per_unit = stop_multiplier * atr
        notional_risk = pct_risk * capital
        units = notional_risk / (risk_per_unit + 1e-12)
        if units < self.cfg['min_units']:
            return 0.0
        # enforce max exposure
        max_units = (self.cfg['max_exposure_pct'] * capital) / price
        return float(max(-max_units, min(max_units, units)))

"""
Risk engine for AlgoSuite.
Provides:
 - position_size(desired_notional, price, capital, history_df)
 - volatility_target sizing
 - simple Kelly / fixed fraction helpers (optional)
 - VaR and CVaR calculations (historical)
Designed to be imported by backtest engine with minimal coupling.
"""

import numpy as np
import pandas as pd

class RiskEngine:
    def __init__(self, cfg=None):
        cfg = cfg or {}
        self.cfg = {
            "position_sizing": cfg.get("position_sizing", "fixed"),  # "fixed"|"vol_target"|"percent_risk"
            "fixed_pct": cfg.get("fixed_pct", 0.1),    # 10% of capital by default for single position
            "vol_target": cfg.get("vol_target", 0.1),  # target annual vol (e.g., 0.1 = 10%)
            "lookback": cfg.get("lookback", 252),
            "pct_risk_per_trade": cfg.get("pct_risk_per_trade", 0.01),
            "min_size": cfg.get("min_size", 0.0),
            "max_size": cfg.get("max_size", 1.0),
        }
    def position_size(self, desired_notional, price, capital, history_df=None):
        """Return number of units (shares/contracts) to hold to reach desired_notional,
        but modulated by sizing strategy and risk controls.
        desired_notional: signed dollar exposure we want (can be negative for short)
        price: current price
        capital: total capital
        history_df: past price DataFrame indexed by timestamp (may be None)
        """
        if price is None or price == 0:
            return 0.0
        desired_pct = desired_notional / (capital + 1e-12)
        # Apply basic bounds
        desired_pct = max(min(desired_pct, self.cfg["max_size"]), -self.cfg["max_size"])
        if self.cfg["position_sizing"] == "fixed":
            # fixed_pct is fraction of capital allocated to a single position (signed)
            target_pct = np.sign(desired_pct) * min(abs(desired_pct), self.cfg["fixed_pct"])
        elif self.cfg["position_sizing"] == "vol_target":
            # adjust allocation based on realized volatility of returns
            if history_df is None or len(history_df) < 2:
                return round((target_pct:=desired_pct) * capital / price, 6)
            close = history_df['close'].dropna().astype(float)
            returns = close.pct_change().dropna()
            ann_vol = returns.std() * np.sqrt(252) if len(returns)>1 else 0.0
            if ann_vol <= 0:
                target_pct = desired_pct
            else:
                target_pct = desired_pct * (self.cfg["vol_target"] / ann_vol)
        elif self.cfg["position_sizing"] == "percent_risk":
            # percent risk per trade => choose position so that stop loss of X% causes pct_risk_per_trade loss
            # requires history to estimate ATR-like metric; fallback to fixed_pct
            if history_df is None or 'high' not in history_df.columns:
                target_pct = np.sign(desired_pct) * min(abs(desired_pct), self.cfg["fixed_pct"])
            else:
                look = history_df.tail(self.cfg["lookback"])
                true_range = (look['high'] - look['low']).abs().dropna()
                volatility = true_range.mean() / (look['close'].mean()+1e-12)
                if volatility <= 0:
                    target_pct = desired_pct
                else:
                    # rough: if stop set at volatility (e.g., 1*vol), position_pct = pct_risk_per_trade / vol
                    target_pct = np.sign(desired_pct) * min(abs(self.cfg["pct_risk_per_trade"] / (volatility+1e-12)), abs(desired_pct))
        else:
            target_pct = desired_pct
        # clamp
        target_pct = max(min(target_pct, self.cfg["max_size"]), -self.cfg["max_size"])
        units = (target_pct * capital) / price
        # floor/min size
        if abs(units) < self.cfg["min_size"]:
            return 0.0
        return units

    # Risk metrics
    def historical_var(self, pnl_series, alpha=0.05):
        """Historical VaR on PnL series: returns positive number representing loss at percentile"""
        pnl = np.asarray(pnl_series).astype(float)
        if len(pnl) == 0:
            return 0.0
        # losses are negative PnL; VaR is positive loss number
        q = np.percentile(-pnl, 100*alpha)
        return float(q)

    def historical_cvar(self, pnl_series, alpha=0.05):
        pnl = np.asarray(pnl_series).astype(float)
        if len(pnl) == 0:
            return 0.0
        losses = -pnl
        thresh = np.percentile(losses, 100*alpha)
        return float(losses[losses>=thresh].mean()) if np.any(losses>=thresh) else float(thresh)

    def volatility_targeting(self, returns_series, target_vol=0.1):
        """Scale factor to apply to exposures to reach target_vol given historical returns"""
        rs = np.asarray(returns_series).astype(float)
        if len(rs) < 2:
            return 1.0
        ann_vol = rs.std() * np.sqrt(252)
        if ann_vol <= 0:
            return 1.0
        return float(target_vol / ann_vol)

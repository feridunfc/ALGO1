from __future__ import annotations
import numpy as np
import pandas as pd
from typing import Dict, Optional

class ProfessionalRiskEngine:
    """
    • Volatility targeting + Kelly fraction
    • Parametric VaR + konsantrasyon + yumuşak korelasyon azaltma
    • ATR bazlı sizing opsiyonu
    """
    def __init__(self, vol_target_annual: float = 0.15, kelly_fraction: float = 0.5,
                 max_concentration: float = 0.3, var_conf: float = 0.95):
        self.vol_target_ann = vol_target_annual
        self.kelly_fraction = kelly_fraction
        self.max_conc = max_concentration
        self.var_conf = var_conf

    @staticmethod
    def atr(ohlc: pd.DataFrame, window: int = 14) -> pd.Series:
        high, low, close = ohlc["high"], ohlc["low"], ohlc["close"]
        prev_close = close.shift(1)
        tr = pd.concat([(high - low).abs(),
                        (high - prev_close).abs(),
                        (low - prev_close).abs()], axis=1).max(axis=1)
        return tr.rolling(window, min_periods=1).mean()

    def position_size(self, signal_strength: float, vol_daily: float,
                      portfolio_value: float, price: float) -> float:
        vol_target_daily = self.vol_target_ann / np.sqrt(252.0)
        raw_size = (vol_target_daily / max(vol_daily, 1e-8)) * float(signal_strength)
        kelly = raw_size * self.kelly_fraction
        dollar = kelly * portfolio_value
        qty = dollar / max(price, 1e-8)
        return max(0.0, float(qty))

    def portfolio_var(self, positions_value: Dict[str, float], cov_daily: pd.DataFrame) -> float:
        if not positions_value:
            return 0.0
        sym = list(positions_value.keys())
        w = np.array([positions_value[s] for s in sym], dtype=float)
        port_val = np.abs(w).sum()
        if port_val <= 0:
            return 0.0
        weights = w / port_val
        cov = cov_daily.loc[sym, sym].values
        vol = np.sqrt(weights @ cov @ weights.T)  # günlük
        z = 1.65 if self.var_conf == 0.95 else 2.33
        return float(z * vol)

    def enforce(self, signals: Dict[str, float], sector_map: Dict[str, str],
                max_sector_weight: float, corr_matrix: Optional[pd.DataFrame] = None) -> Dict[str, float]:
        out = signals.copy()
        # sector cap
        sector_sum: Dict[str, float] = {}
        for s, w in out.items():
            sec = sector_map.get(s, "OTHER")
            sector_sum[sec] = sector_sum.get(sec, 0.0) + abs(w)
        for s, w in list(out.items()):
            sec = sector_map.get(s, "OTHER")
            if sector_sum.get(sec, 0.0) > max_sector_weight:
                out[s] = float(w) * (max_sector_weight / max(sector_sum[sec], 1e-9))
        # correlation soft penalty
        if corr_matrix is not None and not corr_matrix.empty:
            for s, w in list(out.items()):
                if s in corr_matrix.index:
                    avg_corr = corr_matrix.loc[s].drop(labels=[s], errors="ignore").abs().mean()
                    if pd.notna(avg_corr) and avg_corr > 0.8:
                        out[s] *= 0.7
        return out

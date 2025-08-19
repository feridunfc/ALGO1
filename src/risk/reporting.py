
from __future__ import annotations
import numpy as np
import pandas as pd

class RiskReporter:
    def __init__(self, portfolio_state_provider):
        self.state = portfolio_state_provider  # function returning dict: {positions, sector_map, last_prices}

    @staticmethod
    def var_cvar(returns: pd.Series, alpha: float = 0.95):
        if returns is None or returns.empty:
            return 0.0, 0.0
        q = returns.quantile(1 - alpha)
        tail = returns[returns <= q]
        cvar = tail.mean() if len(tail) else q
        return float(-q), float(-cvar)

    def sector_exposure(self):
        st = self.state()
        pos = st.get("positions", {}); sectors = st.get("sector_map", {}); px = st.get("last_prices", {})
        expo = {}
        for sym, qty in pos.items():
            val = qty * px.get(sym, 0.0)
            sec = sectors.get(sym, "UNKNOWN")
            expo[sec] = expo.get(sec, 0.0) + val
        total = sum(abs(v) for v in expo.values()) or 1.0
        return {k: v/total for k, v in expo.items()}

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict
import pandas as pd

@dataclass
class PortfolioState:
    cash: float
    positions: Dict[str, float] = field(default_factory=dict)
    total_value: float = 0.0

class PortfolioManagerEngine:
    def __init__(self, initial_cash: float):
        self.state = PortfolioState(cash=initial_cash)
        self.equity_series = []  # list of (ts, equity)

    def on_fill(self, symbol: str, qty: float, price: float, ts: str):
        pos = self.state.positions.get(symbol, 0.0)
        self.state.positions[symbol] = pos + qty
        cost = qty * price
        self.state.cash -= cost

    def mark_to_market(self, prices: Dict[str, float], ts: str):
        position_value = sum(qty * prices.get(sym, 0.0) for sym, qty in self.state.positions.items())
        self.state.total_value = self.state.cash + position_value
        self.equity_series.append((ts, self.state.total_value))

    def equity(self) -> pd.Series:
        if not self.equity_series:
            return pd.Series(dtype="float64")
        idx, vals = zip(*self.equity_series)
        return pd.Series(vals, index=pd.to_datetime(list(idx)), name="equity").sort_index()

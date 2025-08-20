from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List
from datetime import datetime, timezone


@dataclass
class Fill:
    timestamp: datetime
    symbol: str
    side: str
    qty: float
    price: float
    slippage_bps: float


@dataclass
class PaperExecutionSimulator:
    initial_balance: float = 100_000.0
    commission_bps: float = 1.0
    latency_ms: int = 100
    positions: Dict[str, float] = field(default_factory=dict)
    cash: float = field(default=100_000.0)
    fills: List[Fill] = field(default_factory=list)

    def __post_init__(self):
        self.cash = self.initial_balance

    def _apply_commission(self, notional: float) -> float:
        return notional * (self.commission_bps / 10_000.0)

    def submit_order(
        self,
        symbol: str,
        side: str,
        qty: float,
        price: float,
        slippage_bps: float = 0.0,
    ) -> bool:
        side_u = side.upper()
        exec_price = price * (1 + (slippage_bps / 10_000.0) * (1 if side_u == "BUY" else -1))
        notional = qty * exec_price
        fee = self._apply_commission(abs(notional))

        if side_u == "BUY":
            if self.cash < notional + fee:  # insufficient cash
                return False
            self.cash -= (notional + fee)
            self.positions[symbol] = self.positions.get(symbol, 0.0) + qty
        else:  # SELL
            self.positions[symbol] = self.positions.get(symbol, 0.0) - qty
            self.cash += (abs(notional) - fee)

        # timezone-aware, UTC timestamp (utcnow deprecation fix)
        self.fills.append(
            Fill(datetime.now(timezone.utc), symbol, side_u, qty, exec_price, slippage_bps)
        )
        return True

    def portfolio_value(self, last_prices: Dict[str, float]) -> float:
        value = self.cash
        for sym, q in self.positions.items():
            value += q * last_prices.get(sym, 0.0)
        return value

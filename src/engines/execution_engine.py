from __future__ import annotations
from dataclasses import dataclass

@dataclass
class ExecutionResult:
    quantity: float
    weight: float
    price: float

class ExecutionEngine:
    def __init__(self, fee_bps: float = 2.0, slippage_bps: float = 5.0):
        self.fee_bps = fee_bps
        self.slippage_bps = slippage_bps

    def execute_weight(self, portfolio_value: float, price: float, target_weight: float) -> ExecutionResult:
        # simple paper execution: convert weight to quantity at current price
        notional = portfolio_value * abs(target_weight)
        eff_price = price * (1 + (self.slippage_bps/10000.0))  # buy side approximation
        qty = notional / eff_price
        if target_weight < 0:  # short
            qty = -qty
        return ExecutionResult(quantity=qty, weight=target_weight, price=eff_price)

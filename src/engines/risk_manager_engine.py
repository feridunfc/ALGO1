import math
from dataclasses import dataclass

@dataclass
class RiskParams:
    risk_per_trade_pct: float = 0.01
    atr_multiplier: float = 2.0
    max_position_weight_pct: float = 0.10  # NEW: cap by portfolio weight

class RiskManagerEngine:
    def __init__(self, risk_params: RiskParams | None = None):
        self.risk_params = risk_params or RiskParams()

    def assess_trade(self, side: str, entry_price: float, portfolio_value: float, atr: float | None = None, stop_loss_price: float | None = None):
        rp = self.risk_params
        rationale = []

        if stop_loss_price is None:
            if atr is not None and atr > 0:
                stop_loss_price = entry_price - rp.atr_multiplier * atr if side.upper() == "LONG" else entry_price + rp.atr_multiplier * atr
                rationale.append(f"stop via ATR x{rp.atr_multiplier}")
            else:
                stop_loss_price = entry_price * (0.99 if side.upper() == "LONG" else 1.01)
                rationale.append("stop via 1% fallback")

        if side.upper() == "LONG":
            risk_per_share = max(1e-8, entry_price - stop_loss_price)
        else:
            risk_per_share = max(1e-8, stop_loss_price - entry_price)

        total_risk_amount = max(0.0, portfolio_value * rp.risk_per_trade_pct)
        quantity = math.floor(total_risk_amount / risk_per_share) if risk_per_share > 0 else 0
        position_value = quantity * entry_price

        max_allowed_value = portfolio_value * rp.max_position_weight_pct
        if position_value > max_allowed_value:
            quantity = math.floor(max_allowed_value / entry_price) if entry_price > 0 else 0
            rationale.append(f"position capped by max_position_weight_pct={rp.max_position_weight_pct:.2%}")

        position_size_pct = (quantity * entry_price) / portfolio_value if portfolio_value > 0 else 0.0

        return {
            "quantity": int(quantity),
            "stop_loss_price": float(stop_loss_price),
            "take_profit_price": None,
            "position_size_pct": float(position_size_pct),
            "rationale": "; ".join(rationale) if rationale else "ok",
        }

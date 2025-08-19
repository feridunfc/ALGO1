
from __future__ import annotations
import pandas as pd

def implementation_shortfall(trades: pd.DataFrame, arrival_price: float, side: str) -> float:
    """Positive is worse (more cost for BUY, less proceeds for SELL)."""
    if trades is None or len(trades) == 0 or arrival_price is None:
        return 0.0
    filled_qty = trades["qty"].sum()
    if filled_qty <= 0:
        return 0.0
    avg_fill = (trades["px"] * trades["qty"]).sum() / filled_qty
    if side == "BUY":
        return float((avg_fill - arrival_price) / arrival_price)
    else:
        return float((arrival_price - avg_fill) / arrival_price)

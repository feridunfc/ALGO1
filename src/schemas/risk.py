
from dataclasses import dataclass
from typing import Optional

@dataclass
class RiskDecision:
    approved: bool
    reason: Optional[str] = None
    max_qty: Optional[float] = None
    sl_px: Optional[float] = None
    tp_px: Optional[float] = None

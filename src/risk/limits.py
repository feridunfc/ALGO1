
from __future__ import annotations
from dataclasses import dataclass

@dataclass
class RiskLimits:
    max_drawdown_pct: float = 0.10
    max_pos_per_symbol_pct: float = 0.30

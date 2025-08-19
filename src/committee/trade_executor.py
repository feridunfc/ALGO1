from __future__ import annotations
from typing import Dict, List
from dataclasses import dataclass

@dataclass
class Order:
    symbol: str
    target_weight: float

class TradeExecutor:
    """Mevcut ağırlık → hedef ağırlık farkından emir listesi üretir."""
    def diff(self, current_w: Dict[str, float], target_w: Dict[str, float]) -> List[Order]:
        all_syms = set(current_w) | set(target_w)
        orders = []
        for s in all_syms:
            cur = current_w.get(s, 0.0)
            tgt = target_w.get(s, 0.0)
            if abs(tgt - cur) > 1e-6:
                orders.append(Order(s, tgt))
        return orders

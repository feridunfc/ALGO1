
from __future__ import annotations
from typing import Dict, List, Tuple

def split_across_venues(qty: float, venues_liquidity: Dict[str, float]) -> List[Tuple[str, float]]:
    """Simple proportional split by liquidity score (>=0).
    Return list of (venue, qty).
    """
    if qty <= 0 or not venues_liquidity:
        return []
    total = sum(max(0.0, v) for v in venues_liquidity.values())
    if total <= 0:
        # equal split
        n = len(venues_liquidity)
        return [(v, qty/n) for v in venues_liquidity]
    out = []
    for v, liq in venues_liquidity.items():
        out.append((v, qty * max(0.0, liq)/total))
    return out

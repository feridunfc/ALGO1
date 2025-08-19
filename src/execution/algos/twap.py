
from __future__ import annotations
from typing import List, Dict

def twap_schedule(total_qty: float, n_slices: int) -> List[Dict]:
    if n_slices <= 0 or total_qty <= 0:
        return []
    slice_qty = total_qty / n_slices
    return [{"slice_index": i+1, "qty": slice_qty} for i in range(n_slices)]

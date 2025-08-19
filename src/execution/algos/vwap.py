
from __future__ import annotations
from typing import List, Dict
import numpy as np

def vwap_schedule(total_qty: float, vol_profile: list[float]) -> List[Dict]:
    if total_qty <= 0 or not vol_profile:
        return []
    arr = np.asarray(vol_profile, dtype=float)
    arr = arr.clip(min=0)
    if arr.sum() <= 0:
        # fallback equal weight
        w = np.ones(len(arr)) / len(arr)
    else:
        w = arr / arr.sum()
    return [{"slice_index": i+1, "qty": float(total_qty * w[i])} for i in range(len(arr))]

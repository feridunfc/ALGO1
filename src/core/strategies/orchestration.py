
from __future__ import annotations
from typing import List, Optional
from schemas.signal import Signal

def choose_signal(candidates: List[Optional[Signal]]) -> Optional[Signal]:
    # Basit seçim: ilk None olmayan ve en yüksek strength'li sinyali seç
    nones = [s for s in candidates if s is not None]
    if not nones:
        return None
    nones.sort(key=lambda s: s.strength, reverse=True)
    return nones[0]

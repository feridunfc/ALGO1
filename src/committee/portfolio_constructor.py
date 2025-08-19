from __future__ import annotations
from dataclasses import dataclass
from typing import Dict

@dataclass
class PCConfig:
    max_allocation_per_asset: float = 0.10
    sector_limits: Dict[str, float] | None = None  # {'TECH': 0.3} gibi
    cash_floor: float = 0.05

class PortfolioConstructor:
    """
    Per-asset cap + sector cap + cash floor uygular, kalanını normalize eder.
    """
    def __init__(self, sector_map: Dict[str, str], cfg: PCConfig | None = None):
        self.sector_map = sector_map or {}
        self.cfg = cfg or PCConfig(sector_limits={})

    def construct(self, allowed: Dict[str, float]) -> Dict[str, float]:
        # 1) varlık başına sınır
        capped = {s: min(w, self.cfg.max_allocation_per_asset)
                  for s, w in allowed.items() if w > 0}
        # 2) sektör limitleri
        sec_sum: Dict[str, float] = {}
        for s, w in list(capped.items()):
            sec = self.sector_map.get(s, "UNKNOWN")
            cap = (self.cfg.sector_limits or {}).get(sec, 1.0)
            used = sec_sum.get(sec, 0.0)
            if used + w > cap:
                capped[s] = max(0.0, cap - used)
                w = capped[s]
            sec_sum[sec] = used + w
        total = sum(capped.values())
        if total <= 0:
            return {}
        # 3) nakit tabanı düşülerek normalize et
        scale = max(1e-9, (1.0 - self.cfg.cash_floor) / total)
        return {s: w * scale for s, w in capped.items() if w > 0}

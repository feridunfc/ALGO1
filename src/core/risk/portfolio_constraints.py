from __future__ import annotations
import numpy as np
import pandas as pd
from typing import Dict, Optional

class PortfolioConstraints:
    """Basit portföy-düzeyi kısıtlar:
    - max_allocation_per_asset (cap & renormalize)
    - sector caps (sektör toplam ağırlık limiti)
    - correlation cap (yüksek korelasyonlu çiftlerde zorlama ile azaltma)
    """
    def __init__(self,
                 max_allocation_per_asset: float = 0.15,
                 sector_caps: Optional[Dict[str, float]] = None,
                 corr_cap: Optional[float] = None):
        self.max_alloc = max_allocation_per_asset
        self.sector_caps = sector_caps or {}
        self.corr_cap = corr_cap  # örn. 0.9

    def enforce(self,
                weights: Dict[str, float],
                sector_map: Optional[Dict[str, str]] = None,
                returns_window: Optional[pd.DataFrame] = None) -> Dict[str, float]:
        w = weights.copy()
        # 1) Per-asset cap
        for k in list(w.keys()):
            w[k] = float(min(self.max_alloc, max(0.0, w[k])))
        self._renorm(w)

        # 2) Sector caps
        if sector_map and self.sector_caps:
            by_sector = {}
            for sym, a in w.items():
                sec = sector_map.get(sym, "OTHER")
                by_sector[sec] = by_sector.get(sec, 0.0) + a
            # reduce sectors above caps
            for sec, cap in self.sector_caps.items():
                if by_sector.get(sec, 0.0) > cap:
                    # scale down sector names
                    scale = cap / by_sector[sec]
                    for sym, a in w.items():
                        if sector_map.get(sym, "OTHER") == sec:
                            w[sym] = a * scale
            self._renorm(w)

        # 3) Correlation cap (heuristic)
        if self.corr_cap is not None and returns_window is not None and len(returns_window.columns) > 1:
            C = returns_window.pct_change().dropna().corr().values
            cols = list(returns_window.columns)
            for i in range(len(cols)):
                for j in range(i+1, len(cols)):
                    if C[i, j] >= self.corr_cap:
                        # squeeze the smaller weight among the pair
                        si, sj = cols[i], cols[j]
                        if si in w and sj in w:
                            if w[si] < w[sj]:
                                w[si] *= 0.5
                            else:
                                w[sj] *= 0.5
            self._renorm(w)
        return w

    def _renorm(self, w: Dict[str, float]):
        s = sum(max(0.0, v) for v in w.values())
        if s > 0:
            for k in w:
                w[k] = max(0.0, w[k]) / s

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict
import pandas as pd

@dataclass
class AssetSelectorConfig:
    min_liquidity: float = 1e5
    min_history_days: int = 252
    max_assets: int = 25

class AssetSelector:
    """
    Geniş (wide) fiyat verisinden (close) evren seçer.
    Likidite, tarih uzunluğu ve 3 aylık momentum ile sıralar.
    """
    def __init__(self, price_history: pd.DataFrame,
                 liquidity: pd.Series | None = None,
                 sector_map: Dict[str, str] | None = None,
                 cfg: AssetSelectorConfig | None = None):
        self.price_history = price_history
        self.liquidity = liquidity
        self.sector_map = sector_map or {}
        self.cfg = cfg or AssetSelectorConfig()

    def universe(self) -> List[str]:
        symbols = list(self.price_history.columns)
        if self.liquidity is not None:
            symbols = [s for s in symbols
                       if float(self.liquidity.get(s, 0.0)) >= self.cfg.min_liquidity]
        symbols = [s for s in symbols
                   if self.price_history[s].notna().sum() >= self.cfg.min_history_days]
        # 3 aylık momentum (≈63 iş günü)
        mom = {s: self.price_history[s].pct_change(63).iloc[-1]
               for s in symbols if self.price_history[s].notna().sum() >= 63}
        top = sorted(mom, key=mom.get, reverse=True)[: self.cfg.max_assets]
        return top

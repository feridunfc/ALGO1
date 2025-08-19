# src/core/slippage/volume_weighted.py
from __future__ import annotations
"""
VWAP/ADV tabanlı hacim-etkisi (slippage) yardımcıları.
Basit, ancak kalibre edilebilir formüller içerir.
"""

from dataclasses import dataclass
from typing import Tuple


@dataclass
class VWAPSlippageConfig:
    impact_perc_at_full_adv: float = 0.10  # %10 ADV'de %10 fiyat etkisi (örn.)
    min_slippage_bps: float = 5.0          # taban sürtünme: 5 bps
    clip_bps: float = 150.0                # üst sınır: 150 bps


def volume_weighted_slippage_bps(qty: float, adv: float, cfg: VWAPSlippageConfig | None = None) -> float:
    """
    Basit bir ADV oranı -> bps slippage haritalaması.
    qty/adv oranı 1 olduğunda 'impact_perc_at_full_adv' kadar yüzdesel etki varsayar.
    """
    cfg = cfg or VWAPSlippageConfig()
    if adv <= 0:
        return cfg.clip_bps
    participation = max(0.0, qty / float(adv))  # 0..+
    # lineer basit yaklaşım (istersen log/kuvvet yasası yapabilirsin)
    impact_perc = cfg.impact_perc_at_full_adv * participation
    bps = max(cfg.min_slippage_bps, min(cfg.clip_bps, impact_perc * 1e4))
    return float(bps)


def apply_vwap_slippage(price: float, side: str, qty: float, adv: float,
                        cfg: VWAPSlippageConfig | None = None) -> Tuple[float, float]:
    """
    Fiyatı slipajla ayarla ve bps döndür.
    Return: (slipped_price, slippage_bps)
    """
    bps = volume_weighted_slippage_bps(qty, adv, cfg)
    mult = 1.0 + (bps / 1e4) if side.upper() == "BUY" else 1.0 - (bps / 1e4)
    return price * mult, bps

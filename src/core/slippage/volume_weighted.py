from __future__ import annotations

"""VWAP/ADV tabanlı basit slippage modeli.

Fonksiyonlar
-----------
volume_weighted_slippage_bps(order_qty, adv, impact_factor=0.1, min_bps=5.0) -> float
    Emir büyüklüğü/ADV oranına göre baz puan (bps) cinsinden slippage döndürür.

apply_vwap_slippage(price, side, qty, adv, impact_factor=0.1, min_bps=5.0) -> tuple[float, float]
    Fiyatı slippage ile ayarlayarak dolum fiyatını ve kullanılan bps'i döndürür.
"""

def volume_weighted_slippage_bps(
    order_qty: float,
    adv: float,
    impact_factor: float = 0.1,
    min_bps: float = 5.0,
) -> float:
    if adv is None or adv <= 0 or order_qty is None or order_qty <= 0:
        return float(min_bps)
    # order_qty/adv * (impact_factor * 10_000 bps)
    bps = (order_qty / float(adv)) * (impact_factor * 10_000.0)
    return float(max(min_bps, bps))

def apply_vwap_slippage(
    price: float,
    side: str,
    qty: float,
    adv: float,
    impact_factor: float = 0.1,
    min_bps: float = 5.0,
) -> tuple[float, float]:
    """
    Örnek:
        >>> apply_vwap_slippage(100.0, "BUY", 10_000, 1_000_000)
        (100.1, 10.0)
    """
    bps = volume_weighted_slippage_bps(qty, adv, impact_factor, min_bps)
    slip = float(price) * (bps / 10_000.0)
    is_buy = str(side).upper().startswith("B")
    fill = float(price) + slip if is_buy else float(price) - slip
    return round(fill, 6), round(bps, 4)

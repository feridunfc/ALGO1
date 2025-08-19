from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class EREDecision:
    allowed: bool
    risk_score: float
    position_size_pct: float
    meta: Dict[str, Any]

class EnhancedRiskEngineAdapter:
    """
    Mevcut EnhancedRiskEngine varsa çağırır; yoksa konservatif default döner.
    Çekirdeği değiştirmez.
    """
    def __init__(self, engine: object | None = None):
        self.engine = engine

    def assess(self, symbol: str, features: dict | None = None) -> EREDecision:
        if self.engine is None:
            return EREDecision(True, 0.5, 0.01, {"reason": "default_adapter"})
        try:
            dec = self.engine.evaluate_symbol(symbol, features or {})
            return EREDecision(
                allowed=bool(dec.get("allowed", True)),
                risk_score=float(dec.get("risk_score", 0.5)),
                position_size_pct=float(dec.get("position_size_pct", 0.01)),
                meta=dec
            )
        except Exception as e:
            # Risk motoru hata verirse korumacı davran
            return EREDecision(True, 0.3, 0.005, {"error": str(e)})

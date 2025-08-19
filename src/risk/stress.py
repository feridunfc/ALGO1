
from __future__ import annotations

def shock_return(ret: float, shock: float = -0.1) -> float:
    """Uygulanan şok sonrası tek adımlık getiri"""
    return (1+ret)*(1+shock)-1.0

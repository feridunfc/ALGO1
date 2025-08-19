
from dataclasses import dataclass
from typing import Optional, Literal

Side = Literal["BUY", "SELL", "HOLD"]

@dataclass
class Signal:
    symbol: str
    side: Side
    strength: float = 0.0
    ttl_sec: int = 60
    model: Optional[str] = None

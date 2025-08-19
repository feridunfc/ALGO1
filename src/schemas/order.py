
from dataclasses import dataclass
from typing import Optional, Literal

Side = Literal["BUY", "SELL"]
OrderType = Literal["MARKET", "LIMIT"]

@dataclass
class Order:
    client_id: str
    symbol: str
    side: Side
    type: OrderType
    qty: float
    px: Optional[float] = None

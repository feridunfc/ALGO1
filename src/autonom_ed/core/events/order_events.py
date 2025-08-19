from dataclasses import dataclass
from datetime import datetime
from .base import BaseEvent
from .strategy_events import SignalDirection

@dataclass
class OrderFilled(BaseEvent):
    symbol: str
    timestamp: datetime
    price: float
    target_weight: float
    direction: SignalDirection

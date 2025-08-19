
from dataclasses import dataclass
from .base import BaseEvent
from .strategy_events import SignalDirection

@dataclass
class OrderSubmitted(BaseEvent):
    symbol: str = ""
    direction: SignalDirection = SignalDirection.HOLD
    quantity: float = 0.0

@dataclass
class OrderFilled(BaseEvent):
    symbol: str = ""
    direction: SignalDirection = SignalDirection.HOLD
    quantity: float = 0.0
    fill_price: float = 0.0

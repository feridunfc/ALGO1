from dataclasses import dataclass
from enum import IntEnum
from datetime import datetime
from .base import BaseEvent

class SignalDirection(IntEnum):
    SELL = -1
    HOLD = 0
    BUY = 1

@dataclass
class FeaturesReady(BaseEvent):
    symbol: str
    timestamp: datetime
    features: dict  # single-bar features
    price: float

@dataclass
class StrategySignalGenerated(BaseEvent):
    symbol: str
    timestamp: datetime
    direction: SignalDirection
    meta: dict | None = None

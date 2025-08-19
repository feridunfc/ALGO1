from dataclasses import dataclass
from datetime import datetime
from .base import BaseEvent

@dataclass
class PortfolioReset(BaseEvent):
    starting_equity: float

@dataclass
class PortfolioUpdated(BaseEvent):
    equity: float
    position: float  # current weight
    price: float

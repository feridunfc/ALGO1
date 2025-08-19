from dataclasses import dataclass
from datetime import datetime

from .base import BaseEvent

@dataclass
class BacktestRequested(BaseEvent):
    symbol: str
    start: str
    end: str
    interval: str
    strategy_name: str

@dataclass
class BacktestCompleted(BaseEvent):
    symbol: str
    start: str
    end: str
    interval: str
    strategy_name: str

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any
from .base_event import BaseEvent
from .strategy_events import SignalDirection

@dataclass
class OrderFilled(BaseEvent):
    symbol: str = ""
    strategy_name: str = ""
    direction: SignalDirection = SignalDirection.HOLD
    quantity: float = 0.0
    price: float = 0.0
    weight: float = 0.0  # realized weight on portfolio

@dataclass
class PortfolioUpdated(BaseEvent):
    symbol: str = ""
    total_value: float = 0.0
    cash: float = 0.0
    positions_json: str = ""  # dict(symbol->qty) JSON

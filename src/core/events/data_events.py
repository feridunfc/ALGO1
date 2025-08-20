from __future__ import annotations
from pydantic import Field
from typing import Optional
from .base_event import BaseEvent, EventTopic

class SignalEvent(BaseEvent):
    topic: EventTopic = Field(default=EventTopic.SIGNAL_GENERATED)
    strategy_id: str
    symbol: str
    direction: int     # 1 buy, -1 sell
    strength: float    # 0..1
    confidence: float  # 0..1
    target_size: Optional[float] = None

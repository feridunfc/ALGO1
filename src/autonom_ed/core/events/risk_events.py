from dataclasses import dataclass
from datetime import datetime
from .base import BaseEvent
from .strategy_events import SignalDirection

@dataclass
class RiskAssessmentCompleted(BaseEvent):
    symbol: str
    timestamp: datetime
    direction: SignalDirection
    target_weight: float  # -1..+1 after vol target, constraints applied
    rationale: str = ""

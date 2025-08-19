
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict
from .base_event import BaseEvent

@dataclass(frozen=True)
class RiskViolationDetected(BaseEvent):
    rule: str = ""
    value: float = 0.0
    threshold: float = 0.0
    details: Dict[str, Any] = field(default_factory=dict)

@dataclass(frozen=True)
class CircuitBreakerTriggered(BaseEvent):
    reason: str = ""
    value: float = 0.0

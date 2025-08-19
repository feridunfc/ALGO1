
from __future__ import annotations
from dataclasses import dataclass
from .base_event import BaseEvent

@dataclass(frozen=True)
class ModelSelected(BaseEvent):
    model_name: str = ""

@dataclass(frozen=True)
class UserAction(BaseEvent):
    action: str = ""
    payload: dict | None = None


from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
import uuid
from typing import Any, Dict

@dataclass(frozen=True)
class BaseEvent:
    source: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    correlation_id: str | None = None
    parent_id: str | None = None

    @property
    def event_type(self) -> str:
        return type(self).__name__

    @property
    def version(self) -> str:
        return "1.0"

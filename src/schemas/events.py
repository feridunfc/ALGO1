
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Dict, Any
from datetime import datetime, timezone
import uuid

@dataclass
class Event:
    event_id: str
    timestamp: str
    event_type: str
    source: str
    payload: Dict[str, Any]

    @staticmethod
    def create(event_type: str, source: str, payload: Dict[str, Any]) -> 'Event':
        return Event(
            event_id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc).isoformat(),
            event_type=event_type,
            source=source,
            payload=payload
        )

    def asdict(self) -> Dict[str, Any]:
        return asdict(self)

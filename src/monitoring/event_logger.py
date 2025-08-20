from __future__ import annotations
import json
from pathlib import Path
from datetime import datetime
import asyncio
import logging
from src.core.events import BaseEvent

logger = logging.getLogger("monitor.event_logger")


class EventLogger:
    def __init__(self, log_path: Path):
        self.log_path = Path(log_path)
        self.log_path.mkdir(parents=True, exist_ok=True)
        self._lock = asyncio.Lock()

    async def log_event(self, event: BaseEvent):
        entry = {
            "event_id": event.event_id,
            "topic": getattr(event.topic, "value", str(event.topic)),
            "timestamp": event.timestamp.isoformat(),
            "payload_ref": event.payload_ref,
            "payload_summary": event.payload_summary,
            "payload_digest": event.payload_digest,
            "metadata": event.metadata,
        }
        filename = self.log_path / f"events_{datetime.utcnow().date()}.ndjson"
        async with self._lock:
            with open(filename, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
        logger.debug("Logged event %s %s", entry["topic"], entry["event_id"])

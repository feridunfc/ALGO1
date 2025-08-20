from __future__ import annotations
import json
from pathlib import Path
import asyncio
import logging
from typing import Any

from src.core.event_bus import EnhancedEventBus
from src.core.payload_store import PayloadStore
from src.core.events import BaseEvent, EventTopic
from datetime import datetime

logger = logging.getLogger("tools.replay")


class EventReplayer:
    def __init__(self, event_bus: EnhancedEventBus, payload_store: PayloadStore):
        self.event_bus = event_bus
        self.payload_store = payload_store

    def _parse_log(self, log_file: Path):
        with open(log_file, "r", encoding="utf-8") as f:
            for line in f:
                yield json.loads(line)

    async def replay_events(self, log_file: Path, speed: float = 1.0):
        events = list(self._parse_log(log_file))
        if not events:
            return
        prev_ts = None
        for ev in events:
            ts = ev.get("timestamp")
            delay = 0.0
            if prev_ts is not None and ts:
                try:
                    dt_prev = datetime.fromisoformat(prev_ts)
                    dt_cur = datetime.fromisoformat(ts)
                    delta = (dt_cur - dt_prev).total_seconds()
                    delay = max(0.0, delta / float(speed))
                except Exception:
                    delay = 0.0
            prev_ts = ts

            topic_value = ev.get("topic")
            try:
                topic = EventTopic(topic_value)
            except Exception:
                topic = topic_value

            reconstructed = BaseEvent(
                event_id=ev.get("event_id"),
                topic=topic,
                timestamp=datetime.fromisoformat(ev.get("timestamp")) if ev.get("timestamp") else datetime.utcnow(),
                payload_ref=ev.get("payload_ref"),
                payload_summary=ev.get("payload_summary"),
                payload_digest=ev.get("payload_digest"),
                metadata=ev.get("metadata", {}),
            )
            await self.event_bus.publish(topic, reconstructed)
            if delay > 0:
                await asyncio.sleep(delay)

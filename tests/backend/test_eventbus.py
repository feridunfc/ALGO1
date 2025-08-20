
import asyncio
import pytest

# Robust imports across layouts
try:
    from src.core.event_bus import EnhancedEventBus
    from src.core.events import BaseEvent, EventTopic
except Exception:  # fallback legacy paths
    from core.event_bus import EnhancedEventBus
    from core.events import BaseEvent, EventTopic

class DummyEvent(BaseEvent):
    topic: EventTopic = EventTopic.HEARTBEAT

@pytest.mark.asyncio
async def test_event_publish_and_subscribe():
    bus = EnhancedEventBus(max_workers=2, max_queue_size=1000)
    received = []

    def sync_handler(ev):
        received.append(ev.event_id)

    bus.subscribe(EventTopic.HEARTBEAT, sync_handler)
    await bus.start()
    try:
        ev = DummyEvent()
        await bus.publish(EventTopic.HEARTBEAT, ev)
        # give executor time
        await asyncio.sleep(0.05)
        assert received and received[0] == ev.event_id
    finally:
        await bus.stop()

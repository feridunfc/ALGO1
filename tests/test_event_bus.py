
import asyncio
import pytest
from core.event_bus import EventBus, BaseEvent, DropPolicy

class TestEvt(BaseEvent):
    pass

@pytest.mark.asyncio
async def test_priority_and_once_and_sticky():
    bus = EventBus(sticky_events=True)
    got = []
    def low(e): got.append("low")
    def high(e): got.append("high")
    bus.subscribe(TestEvt, low, priority=1)
    bus.subscribe(TestEvt, high, priority=10, once=True)
    bus.publish(TestEvt(source="t"))
    await asyncio.sleep(0.05)
    assert got == ["high", "low"]
    def late(e): got.append("late")
    bus.subscribe(TestEvt, late, priority=5, replay_sticky=True)
    await asyncio.sleep(0.05)
    assert got[-1] == "late"

@pytest.mark.asyncio
async def test_drop_policy():
    bus = EventBus(max_queue=1, drop_policy=DropPolicy.DROP_NEW)
    bus.publish(TestEvt(source="t1"))
    bus.publish(TestEvt(source="t2"))
    await asyncio.sleep(0.05)
    assert bus.metrics["dropped"] >= 1

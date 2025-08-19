
import os, sys, pandas as pd, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from infra.event_bus import EventBus
from monitoring.metrics import REGISTRY
from monitoring.event_instrumentation import EventInstrumentation
from schemas.events import Event

def test_event_counters_and_lag():
    bus = EventBus()
    EventInstrumentation(bus, topics=["MARKET_DATA","SIGNAL"])
    # Publish two events
    bus.publish("MARKET_DATA", Event.create("MARKET_DATA","t", {"x":1}).asdict())
    bus.publish("SIGNAL", Event.create("SIGNAL","t", {"x":2}).asdict())
    txt = REGISTRY.to_prometheus_text()
    assert "events_total" in txt
    assert 'topic="MARKET_DATA"' in txt or 'topic="SIGNAL"' in txt

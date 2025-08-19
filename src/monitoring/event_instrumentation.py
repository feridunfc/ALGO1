
from __future__ import annotations
from monitoring.metrics import REGISTRY

class EventInstrumentation:
    def __init__(self, bus, topics):
        for t in topics:
            bus.subscribe(t, lambda ev, t=t: REGISTRY.counter("events_total", labels=["topic"]).inc(1, topic=t))

# src/anomaly/alert_handler.py
from typing import Callable, List
from .detector import AnomalyAlert

class AlertHandler:
    def __init__(self, sinks: List[Callable[[AnomalyAlert], None]] = None):
        self.sinks = sinks or []

    def add_sink(self, sink: Callable[[AnomalyAlert], None]):
        self.sinks.append(sink)

    def handle(self, alert: AnomalyAlert):
        for s in self.sinks:
            try:
                s(alert)
            except Exception:
                pass

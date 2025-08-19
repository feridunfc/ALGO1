
from __future__ import annotations
from typing import Dict, Any, Callable
from schemas.events import Event
from risk.limits import RiskLimits

class RiskGate:
    def __init__(self, bus, broker_snapshot_fn: Callable[[], dict] | None, limits: RiskLimits):
        self.bus = bus; self.limits = limits
        bus.subscribe("SIGNAL", self.on_signal)

    def on_signal(self, ev: Dict[str, Any]):
        sig = ev.get("payload", {}).get("signal")
        if not sig: return
        approved = dict(sig); approved["size"] = approved.pop("size_hint", 0.1)
        self.bus.publish("SIGNAL_APPROVED", Event.create("RISK","gate", {"signal": approved}).asdict())


from __future__ import annotations
from typing import Dict, Any
import uuid
from schemas.events import Event

class EMS:
    def __init__(self, bus, default_algo: str = "TWAP", bars_per_parent: int = 1):
        self.bus = bus
        bus.subscribe("SIGNAL_APPROVED", self.on_approved)

    def on_approved(self, ev: Dict[str, Any]):
        sig = ev.get("payload", {}).get("signal")
        if not sig: return
        coid = str(uuid.uuid4())
        order = {"client_order_id": coid, "symbol": sig["symbol"], "side": sig["side"], "qty": sig.get("size", 0.1)}
        self.bus.publish("ORDER_NEW", Event.create("ORDER","ems", {"order": order}).asdict())

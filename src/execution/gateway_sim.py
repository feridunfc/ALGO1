
from __future__ import annotations
from typing import Dict, Any
from schemas.events import Event

class ExchangeGatewaySim:
    def __init__(self, bus):
        self.bus = bus
        bus.subscribe("ORDER_NEW", self.on_new)

    def on_new(self, ev: Dict[str, Any]):
        order = ev.get("payload", {}).get("order")
        if not order: return
        ack = {"client_order_id": order.get("client_order_id"), "status":"ACK"}
        self.bus.publish("ORDER_ACK", Event.create("ORDER","gw_sim", {"ack": ack}).asdict())


from __future__ import annotations
from typing import Dict, Any
from infra.rate_limiter import TokenBucket
from infra.retry import retry
from schemas.events import Event

class CCXTGatewayStub:
    def __init__(self, bus, venue_name: str = "BINANCE", rps: float = 5.0, simulate_fill: bool = True):
        self.bus = bus
        self.venue = venue_name
        self.tb = TokenBucket(rate_per_sec=rps, capacity=rps)
        self.simulate_fill = simulate_fill
        bus.subscribe("ORDER_NEW", self.on_order_new)
        bus.subscribe("MARKET_DATA", self.on_market)
        self._pend = {}
        self._last_bar = {}

    def on_order_new(self, ev: Dict[str, Any]):
        order = ev.get("payload", {}).get("order")
        if not order:
            return
        if not self.tb.take(1.0):
            nack = {"client_order_id": order.get("client_order_id"), "status": "RATE_LIMIT"}
            self.bus.publish("ORDER_ACK", Event.create("ORDER", "ccxt_stub", {"ack": nack}).asdict())
            return

        def _submit():
            return {"status":"ok"}
        retry(_submit, attempts=3, backoff_sec=0.01)

        ack = {"client_order_id": order.get("client_order_id"), "status": "ACKNOWLEDGED"}
        self.bus.publish("ORDER_ACK", Event.create("ORDER", "ccxt_stub", {"ack": ack}).asdict())
        if self.simulate_fill:
            sym = order["symbol"]
            self._pend.setdefault(sym, []).append(order)

    def on_market(self, ev: Dict[str, Any]):
        payload = ev.get("payload", {})
        sym = payload.get("symbol")
        bar = payload.get("bar")
        if not sym or not bar:
            return
        self._last_bar[sym] = bar
        if not self.simulate_fill:
            return
        pend = self._pend.pop(sym, [])
        if pend:
            open_px = float(bar["o"])
            for order in pend:
                trade = {
                    "symbol": sym,
                    "side": order["side"],
                    "qty": float(order["qty"]),
                    "px": open_px,
                    "fee": 0.0,
                    "t": bar["t"],
                    "venue": order.get("venue", self.venue),
                }
                self.bus.publish("BROKER_TRADE", Event.create("ORDER", "ccxt_stub", {"trade": trade}).asdict())

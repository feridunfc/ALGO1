
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from schemas.events import Event
from schemas.signal import Signal
from schemas.order import Order
from schemas.risk import RiskDecision
from infra.serializer import to_json, from_json

def run():
    sig = Signal(symbol="BTC-USD", side="BUY", strength=0.72, ttl_sec=30, model="lstm_v1")
    ord = Order(client_id="sig-abc", symbol="BTC-USD", side="BUY", type="LIMIT", qty=0.1, px=60000.0)
    risk = RiskDecision(approved=True, reason=None, max_qty=0.1, sl_px=58500.0, tp_px=61200.0)

    ev = Event.create(
        event_type="SIGNAL",
        source="core.pipeline",
        payload={
            "signal": sig.__dict__,
            "order": ord.__dict__,
            "risk": risk.__dict__
        }
    )

    s = to_json(ev.asdict())
    data = from_json(s)

    assert data["_schema_version"] == "1.0.0"
    assert data["event_type"] == "SIGNAL"
    assert data["payload"]["signal"]["side"] == "BUY"
    assert abs(data["payload"]["risk"]["sl_px"] - 58500.0) < 1e-9
    print("schema_roundtrip_ok")

if __name__ == "__main__":
    run()

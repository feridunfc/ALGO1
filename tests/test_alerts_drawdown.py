
import os, sys, pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from infra.event_bus import EventBus
from monitoring.alerts import AlertManager
from schemas.events import Event

def test_drawdown_alert_fires():
    bus = EventBus()
    alerts = []
    bus.subscribe("ALERT", lambda ev: alerts.append(ev))
    AlertManager(bus, dd_threshold=0.05)  # 5%
    eqs = [100, 102, 101, 95]  # ~-6.86% drawdown from 102 to 95
    for i, e in enumerate(eqs):
        bus.publish("EQUITY", Event.create("RISK","broker",{ "t": f"t{i}", "equity": e }).asdict())
    assert any(a["payload"]["alert"]["type"]=="DRAWDOWN" for a in alerts)

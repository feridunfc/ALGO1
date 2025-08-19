
import os, sys, pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from data_layer.replayer import DataReplayer
from infra.event_bus import EventBus

def test_replayer_sync():
    df = pd.DataFrame({
        "timestamp": pd.to_datetime(["2023-01-02","2023-01-03"], utc=True),
        "symbol":["BTC-USD","BTC-USD"],
        "open":[1,2],"high":[2,3],"low":[0.5,1.5],"close":[1.5,2.5],"volume":[10,11]
    })
    bus = EventBus()
    received = []
    bus.subscribe("MARKET_DATA", lambda ev: received.append(ev))
    cnt = DataReplayer(df).run_sync(bus)
    assert cnt == 2 and len(received) == 2
    assert received[0]["payload"]["bar"]["o"] == 1.0
    assert received[1]["payload"]["bar"]["c"] == 2.5

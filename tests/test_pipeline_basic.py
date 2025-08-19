
import os, sys, pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from infra.event_bus import EventBus
from data_layer.replayer import DataReplayer
from core.pipeline import CorePipeline

def test_pipeline_generates_signals():
    # Create a simple dataset with a moving average crossover
    prices = list(range(1, 60)) + [30]*20  # up then flat/down-ish to trigger cross changes
    df = pd.DataFrame({
        "timestamp": pd.date_range("2023-01-01", periods=len(prices), freq="T", tz="UTC"),
        "symbol":["BTC-USD"]*len(prices),
        "open":prices, "high":[p+1 for p in prices], "low":[max(0,p-1) for p in prices], "close":prices, "volume":[10]*len(prices)
    })
    bus = EventBus()
    pipeline = CorePipeline(bus)
    signals = []
    bus.subscribe("SIGNAL", lambda ev: signals.append(ev))
    # replay
    DataReplayer(df).run_sync(bus)
    assert len(signals) >= 1
    # check event schema basics
    ev = signals[-1]
    assert ev["event_type"] == "SIGNAL"
    assert "signal" in ev["payload"]
    assert ev["payload"]["signal"]["symbol"] == "BTC-USD"

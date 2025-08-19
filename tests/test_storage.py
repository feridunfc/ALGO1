
import os, sys, pandas as pd, numpy as np
from datetime import datetime, timezone
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from data_layer.storage import DataStorage

def test_storage_roundtrip(tmp_dir="/mnt/data/tmp_store"):
    os.makedirs(tmp_dir, exist_ok=True)
    store = DataStorage(tmp_dir)
    df = pd.DataFrame({
        "timestamp": pd.to_datetime(["2023-01-02","2023-01-03"], utc=True),
        "symbol":["BTC-USD","BTC-USD"],
        "open":[1,2],"high":[2,3],"low":[0.5,1.5],"close":[1.5,2.5],"volume":[10,11]
    })
    p = store.write(df, symbol="BTC-USD", timeframe="1d")
    out = store.read("BTC-USD","1d")
    assert len(out) == 2
    assert abs(float(out["close"].iloc[-1]) - 2.5) < 1e-9

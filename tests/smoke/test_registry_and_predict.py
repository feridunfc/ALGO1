import pandas as pd
from src.strategies.registry import STRATEGY_REGISTRY
from pathlib import Path

def test_all_strategies_predict():
    df = pd.read_csv("tests/fixtures/golden_sample.csv", parse_dates=["timestamp"], index_col="timestamp")
    # ensure minimal OHLCV exists
    assert all(c in df.columns for c in ["open","high","low","close","volume"])
    tested = 0
    for name, Cls in STRATEGY_REGISTRY.items():
        s = Cls()
        if hasattr(s, "fit"):
            try:
                s.fit(df.iloc[:150])
            except Exception:
                pass
        p = s.predict_proba(df.iloc[150:])  # inference slice
        assert len(p) == len(df.iloc[150:])
        assert p.min() >= 0.0 and p.max() <= 1.0
        tested += 1
    assert tested >= 25  # 10 AI + 10 rule + 5 hybrid


import os, sys, pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from backtest.simulator import run_backtest
from backtest.walkforward import walk_forward_backtest

def test_backtest_and_wfa():
    # synthetic: uptrend then downtrend to trigger MA/BB signals
    prices = list(range(1, 200)) + [80]*60 + list(range(70, 110))  # variability
    df = pd.DataFrame({
        "timestamp": pd.date_range("2023-01-01", periods=len(prices), freq="T", tz="UTC"),
        "symbol":["BTC-USD"]*len(prices),
        "open":prices, "high":[p+1 for p in prices], "low":[max(0,p-1) for p in prices], "close":prices, "volume":[10]*len(prices)
    })
    res = run_backtest(df)
    assert "stats" in res and res["stats"]["trades"] >= 1
    assert res["equity"]["equity"].iloc[-1] > 0
    # WFA
    folds = walk_forward_backtest(df, n_splits=3)
    assert len(folds) == 3
    for f in folds:
        assert "stats" in f and "sharpe" in f["stats"]

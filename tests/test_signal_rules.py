
import os, sys, pandas as pd, numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from core.strategies.rules_ma_cross import signal_ma_crossover

def test_ma_cross_buy_and_sell():
    # construct series where 20MA crosses above 50MA then later below
    close = list(range(1, 200))  # upward trend
    # then a sudden drop to force sell
    close += [50]*30
    df = pd.DataFrame({
        "timestamp": pd.date_range("2023-01-01", periods=len(close), freq="D", tz="UTC"),
        "symbol": ["AAA"]*len(close),
        "open": close, "high": [c+1 for c in close], "low": [max(c-1,0) for c in close], "close": close, "volume":[100]*len(close)
    })
    buy = signal_ma_crossover(df.iloc[:120], 20, 50, "AAA")
    assert buy is not None and buy.side == "BUY"
    sell = signal_ma_crossover(df, 20, 50, "AAA")
    assert sell is not None and sell.side in ("SELL",)  # expect a sell at the end

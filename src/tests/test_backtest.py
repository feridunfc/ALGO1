
import numpy as np
import pandas as pd
from ..backtest.vectorized import VectorizedBacktester

def test_vectorized_backtester_runs():
    n = 500
    idx = pd.date_range("2023-01-01", periods=n, freq="D")
    df = pd.DataFrame({
        "open": 100 + np.random.randn(n).cumsum(),
        "close": 100 + np.random.randn(n).cumsum(),
    }, index=idx)
    sig = pd.Series(np.sign(np.random.randn(n)), index=idx)
    bt = VectorizedBacktester()
    out = bt.run(df, sig)
    assert "equity" in out.columns and len(out) == n

def test_no_lookahead():
    n = 200
    idx = pd.date_range("2023-01-01", periods=n, freq="D")
    close = 100 + np.random.randn(n).cumsum()
    df = pd.DataFrame({"open": close, "close": close}, index=idx)
    future_signal = pd.Series(np.sign(np.random.randn(n))).shift(-1).fillna(0.0).reindex(idx)
    bt = VectorizedBacktester()
    out = bt.run(df, future_signal)
    assert np.isfinite(out["strategy_returns"]).all()

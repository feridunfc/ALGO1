
import os, sys, pandas as pd, numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from backtest.metrics import compute_returns, sharpe, max_drawdown, sortino, summarize

def test_metrics_sanity():
    # equity with upward drift + small noise
    np.random.seed(0)
    ret = np.random.normal(0.001, 0.01, size=300)
    equity = pd.Series((1+pd.Series(ret)).cumprod()*100_000.0)
    R = compute_returns(equity)
    sh = sharpe(R, ann_factor=252.0)
    dd = max_drawdown(equity)
    so = sortino(R, ann_factor=252.0)
    s = summarize(equity, trades=pd.DataFrame({"pnl":[1,-0.5,2]}), freq="D")
    assert sh > 0
    assert -0.5 < dd <= 0
    assert so > 0
    assert "total_return" in s and "sharpe" in s and "max_drawdown" in s


import time, numpy as np, pandas as pd
from backtest.vectorized import vectorized_pnl

def generate_large_dataset(n=200_000):
    idx = pd.date_range('2020-01-01', periods=n, freq='T')
    close = 100*(1+0.00005*np.random.randn(n)).cumprod()
    df = pd.DataFrame({'open':close, 'high':close*1.001, 'low':close*0.999, 'close':close, 'volume':1_000}, index=idx)
    sig = pd.Series(np.sign(np.random.randn(n)), index=idx).rolling(10).mean().apply(lambda x: 1 if x>0 else (-1 if x<0 else 0))
    return df, sig

def test_backtest_performance():
    df, sig = generate_large_dataset(50_000)
    t0 = time.time()
    equity, ret = vectorized_pnl(df, sig)
    dt = time.time() - t0
    assert dt < 2.5, f"Vectorized too slow: {dt:.2f}s for {len(df)} rows"
    assert np.isfinite(equity.iloc[-1])

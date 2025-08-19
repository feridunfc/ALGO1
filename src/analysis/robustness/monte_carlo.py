
import numpy as np
import pandas as pd

def block_bootstrap(series: pd.Series, block: int = 20, size: int | None = None, seed: int = 42) -> pd.Series:
    rng = np.random.default_rng(seed)
    n = len(series)
    size = size or n
    idx = []
    while len(idx) < size:
        start = rng.integers(0, max(1, n - block))
        idx.extend(range(start, min(n, start + block)))
    idx = idx[:size]
    return series.iloc[idx].reset_index(drop=True)

def monte_carlo_equity(equity: pd.Series, trials: int = 100, block: int = 20, seed: int = 42) -> pd.DataFrame:
    rows = []
    for t in range(trials):
        boot = block_bootstrap(equity.pct_change().dropna(), block=block, seed=seed+t)
        curve = (1 + boot).cumprod()
        rows.append({
            "trial": t, "ret": float(curve.iloc[-1] - 1.0),
            "max_dd": float((curve/curve.cummax() - 1.0).min())
        })
    return pd.DataFrame(rows)

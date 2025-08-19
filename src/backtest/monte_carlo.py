
from __future__ import annotations
import numpy as np
import pandas as pd

def bootstrap_paths(returns: pd.Series, n_paths: int = 500, path_len: int | None = None, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    r = returns.dropna().to_numpy()
    if path_len is None:
        path_len = len(r)
    paths = []
    for _ in range(n_paths):
        boot = rng.choice(r, size=path_len, replace=True)
        equity = (1.0 + pd.Series(boot)).cumprod()
        paths.append(equity.values)
    return pd.DataFrame(paths).T  # time x n_paths

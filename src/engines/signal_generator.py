from __future__ import annotations
import numpy as np, pandas as pd

def vectorized_ma_signals(feat: pd.DataFrame) -> pd.Series:
    fast = feat["ma_fast"]
    slow = feat["ma_slow"]
    spread = fast - slow
    direction = np.sign(spread).fillna(0.0)
    return direction.astype(float)

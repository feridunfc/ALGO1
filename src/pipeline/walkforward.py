from __future__ import annotations
import numpy as np
import pandas as pd
from sklearn.model_selection import TimeSeriesSplit
from typing import Callable, Dict, Any, Tuple

def run_walkforward(df: pd.DataFrame,
                    make_signal_fn: Callable[[pd.DataFrame, Tuple[int,int]], pd.Series],
                    n_splits: int = 5) -> Dict[str, Any]:
    """
    make_signal_fn: (df, (train_idx, test_idx)) -> signal (aligned to df.index, NaN outside test)
    """
    tscv = TimeSeriesSplit(n_splits=n_splits)
    parts = []
    for tr_idx, te_idx in tscv.split(df):
        tr = df.iloc[tr_idx]
        te = df.iloc[te_idx]
        sig = make_signal_fn(df, (tr_idx, te_idx))
        # keep only test slice
        parts.append(sig.iloc[te_idx])
    full_sig = pd.concat(parts).reindex(df.index).fillna(0.0)
    return {"signal": full_sig}

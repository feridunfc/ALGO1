
from __future__ import annotations
from typing import Any, Dict
import pandas as pd
import numpy as np

class BaseStrategy:
    family: str = "conventional"
    is_strategy: bool = True
    trainable: bool = False

    def __init__(self, params: Dict[str, Any] | None = None):
        self.params = params or {}

    def fit(self, df: pd.DataFrame) -> None:
        return None

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        raise NotImplementedError

    @staticmethod
    def _to_series_1d(x, index) -> pd.Series:
        if isinstance(x, pd.Series):
            return x.reindex(index)
        if isinstance(x, pd.DataFrame):
            if x.shape[1] != 1:
                x = x.iloc[:,0]
            else:
                x = x.squeeze("columns")
            return x.reindex(index)
        x = np.asarray(x).reshape(-1)
        return pd.Series(x, index=index, name="signal")

    @staticmethod
    def _pct_change(s: pd.Series, periods: int = 1) -> pd.Series:
        return s.pct_change(periods=periods, fill_method=None)

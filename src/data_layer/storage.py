
from __future__ import annotations
import os
from pathlib import Path
from typing import Optional
import pandas as pd

try:
    import pyarrow  # noqa: F401
    _HAS_PARQUET = True
except Exception:
    _HAS_PARQUET = False

class DataStorage:
    """Simple symbol/timeframe based storage. Falls back to CSV if parquet unavailable."""
    def __init__(self, base_dir: str):
        self.base = Path(base_dir)
        self.base.mkdir(parents=True, exist_ok=True)

    def _file_path(self, symbol: str, timeframe: str, fmt: Optional[str] = None) -> Path:
        fmt = (fmt or ("parquet" if _HAS_PARQUET else "csv")).lower()
        fname = f"{symbol.replace('/','-')}_{timeframe}.{fmt}"
        return self.base / fname

    def write(self, df: pd.DataFrame, symbol: str, timeframe: str, fmt: Optional[str] = None) -> Path:
        p = self._file_path(symbol, timeframe, fmt)
        p.parent.mkdir(parents=True, exist_ok=True)
        if p.suffix == ".parquet":
            df.to_parquet(p, index=False)
        else:
            df.to_csv(p, index=False)
        return p

    def read(self, symbol: str, timeframe: str) -> pd.DataFrame:
        # try parquet then csv
        p_parq = self._file_path(symbol, timeframe, "parquet")
        p_csv  = self._file_path(symbol, timeframe, "csv")
        if p_parq.exists():
            return pd.read_parquet(p_parq)
        if p_csv.exists():
            return pd.read_csv(p_csv, parse_dates=["timestamp"])
        return pd.DataFrame()

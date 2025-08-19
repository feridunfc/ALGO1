from __future__ import annotations
import pandas as pd
import numpy as np
from typing import Optional
import yfinance as yf

class DataProviderEngine:
    def fetch(self, symbol: str, start: Optional[str], end: Optional[str], interval: str) -> pd.DataFrame:
        df = yf.download(symbol, start=start, end=end, interval=interval, progress=False, auto_adjust=True)
        if isinstance(df.columns, pd.MultiIndex):
            # yfinance sometimes returns multiindex (symbol, field)
            df = df.droplevel(0, axis=1)
        # Standardize columns
        rename = {c: c.lower() for c in df.columns}
        df = df.rename(columns=rename)
        required = {"open","high","low","close","volume"}
        missing = required - set(df.columns)
        if missing:
            raise ValueError(f"yfinance returned unexpected columns. Missing: {missing}")
        # Ensure numeric dtypes
        df = df.astype({c:"float64" for c in required})
        df["ret"] = df["close"].pct_change().fillna(0.0)
        return df

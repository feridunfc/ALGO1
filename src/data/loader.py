from __future__ import annotations
import pandas as pd
import numpy as np
from typing import Optional, Dict
from datetime import datetime
from core.data_normalizer import FinancialDataNormalizer, NormalizationConfig, NormalizationMethod, NaNPolicy

def _try_import_yf():
    try:
        import yfinance as yf  # type: ignore
        return yf
    except Exception:
        return None

def load_ohlcv(source: str = "yfinance", symbol: str = "BTC-USD", start: Optional[str] = None, end: Optional[str] = None, interval: str = "1d") -> pd.DataFrame:
    """Load OHLCV with a standardized schema and timezone-aware index."""
    if source == "yfinance":
        yf = _try_import_yf()
        if yf is None:
            # fallback synthetic
            idx = pd.date_range(start or "2021-01-01", end or "2021-12-31", freq="B", tz="UTC")
            base = 100 + np.cumsum(np.random.randn(len(idx)))
            df = pd.DataFrame({
                "open": base + np.random.randn(len(idx))*0.1,
                "high": base + np.random.rand(len(idx))*0.2,
                "low":  base - np.random.rand(len(idx))*0.2,
                "close": base + np.random.randn(len(idx))*0.1,
                "volume": np.random.randint(1e5, 5e5, size=len(idx)),
            }, index=idx)
            return df
        df = yf.download(symbol, start=start, end=end, interval=interval, auto_adjust=True, progress=False)
        if df.empty:
            raise ValueError("yfinance returned empty dataframe")
        df = df.rename(columns={"Open":"open","High":"high","Low":"low","Close":"close","Volume":"volume"})
        if df.index.tz is None:
            df.index = df.index.tz_localize("UTC")
        return df[["open","high","low","close","volume"]].sort_index()
    elif source in {"csv","parquet"}:
        raise NotImplementedError("CSV/Parquet loader stub — plug your path here")
    else:
        raise ValueError(f"Unknown source: {source}")

def normalize_ohlcv(df: pd.DataFrame) -> pd.DataFrame:
    """Enforce FinancialDataNormalizer (ZSCORE/ROBUST)."""
    cfg = NormalizationConfig(
        method=NormalizationMethod.ROBUST,
        nan_policy=NaNPolicy.FFILL,
        clip_outliers=True,
    )
    norm = FinancialDataNormalizer(cfg)
    # We only normalize columns that need scaling; keep close for later metrics as is.
    scaled = norm.fit_transform(df[["open","high","low","volume"]])
    out = df.copy()
    out[["open","high","low","volume"]] = scaled.values
    return out
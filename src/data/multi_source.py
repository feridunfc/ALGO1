
import pandas as pd
from .validation import normalize_ohlc_columns, ensure_timezone

def load_csv(path: str, tz: str = "UTC") -> pd.DataFrame:
    df = pd.read_csv(path)
    if "date" in df.columns and not isinstance(df.index, pd.DatetimeIndex):
        df["date"] = pd.to_datetime(df["date"])
        df = df.set_index("date")
    df = normalize_ohlc_columns(df)
    df = ensure_timezone(df, tz)
    return df

def load_parquet(path: str, tz: str = "UTC") -> pd.DataFrame:
    df = pd.read_parquet(path)
    if "date" in df.columns and not isinstance(df.index, pd.DatetimeIndex):
        df["date"] = pd.to_datetime(df["date"])
        df = df.set_index("date")
    df = normalize_ohlc_columns(df)
    df = ensure_timezone(df, tz)
    return df

def load_yfinance(symbol: str, start=None, end=None, interval="1d", tz: str = "UTC") -> pd.DataFrame:
    try:
        import yfinance as yf
    except Exception:
        raise RuntimeError("yfinance not installed")
    df = yf.download(symbol, start=start, end=end, interval=interval, progress=False)
    df.columns = [c.lower() for c in df.columns]
    # yfinance may return timezone-aware; normalize
    if isinstance(df.index, pd.DatetimeIndex):
        df.index = df.index.tz_localize(None)
    df = ensure_timezone(df, tz)
    return df

def load_binance_klines(symbol: str, interval: str = "1h", limit: int = 1000) -> pd.DataFrame:
    # Placeholder client: returns synthetic but shape-compatible DF.
    import numpy as np
    rng = pd.date_range("2023-01-01", periods=limit, freq=interval.upper())
    df = pd.DataFrame({
        "open": 100 + np.random.randn(limit).cumsum(),
        "high": 100 + np.random.randn(limit).cumsum() + 1.0,
        "low":  100 + np.random.randn(limit).cumsum() - 1.0,
        "close":100 + np.random.randn(limit).cumsum(),
        "volume": np.random.randint(100, 10000, size=limit)
    }, index=rng)
    return df

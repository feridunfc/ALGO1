from __future__ import annotations
from typing import Dict, Any, Tuple
import numpy as np, pandas as pd

def validate_ohlc(df: pd.DataFrame) -> bool:
    req = ["open","high","low","close","volume"]
    if not all(c in df.columns for c in req):
        return False
    if (df["high"] < df["low"]).any(): return False
    if (df["close"] > df["high"]).any(): return False
    if (df["close"] < df["low"]).any(): return False
    return True

def _synthetic_ohlc(n=800, seed=42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    ret = rng.normal(0, 0.01, n)
    price = 100 * (1 + pd.Series(ret)).cumprod()
    high = price * (1 + rng.normal(0.002, 0.002, n))
    low = price * (1 - rng.normal(0.002, 0.002, n))
    open_ = price.shift(1).fillna(price.iloc[0])
    vol = rng.integers(100, 1000, n)
    idx = pd.date_range(end=pd.Timestamp.utcnow().normalize(), periods=n, freq="D")
    return pd.DataFrame({"open":open_,"high":high,"low":low,"close":price,"volume":vol}, index=idx)

def fetch_ohlc(source: str, symbol: str, start, end, freq="1d", seed=42):
    if source == "synthetic":
        df = _synthetic_ohlc(n=max(300, (end - start).days), seed=seed)
        return df.loc[(df.index >= start) & (df.index <= end)]
    # yfinance
    try:
        import yfinance as yf
        df = yf.download(symbol, start=start, end=end, interval={"1d":"1d","1h":"60m","30min":"30m"}.get(freq,"1d"))
        df = df.rename(columns={"Open":"open","High":"high","Low":"low","Close":"close","Volume":"volume"})
        df = df[["open","high","low","close","volume"]].dropna()
        return df
    except Exception:
        return _synthetic_ohlc(n=max(300, (end - start).days), seed=seed)

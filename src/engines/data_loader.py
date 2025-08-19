from __future__ import annotations
import logging
from typing import Optional
import pandas as pd

logger = logging.getLogger("DataLoader")

def _normalize_ohlcv(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out.columns = [c.lower().replace(" ", "") for c in out.columns]
    if "adjclose" in out.columns and "close" in out.columns:
        out["close"] = out["adjclose"]
    keep = [c for c in ["open","high","low","close","volume"] if c in out.columns]
    out = out[keep].dropna()
    out.index = pd.to_datetime(out.index, utc=True)
    for c in keep:
        out[c] = pd.to_numeric(out[c], errors="coerce")
    out = out.dropna()
    return out

def _validate_ohlc(df: pd.DataFrame) -> bool:
    ok = (df["high"] >= df["low"]).all() and (df["close"] <= df["high"]).all() and (df["close"] >= df["low"]).all()
    if not ok:
        bad = (~((df["high"] >= df["low"]) & (df["close"] <= df["high"]) & (df["close"] >= df["low"]))).sum()
        logger.error("OHLC validation failed on %s rows", bad)
    return ok

class DataLoader:
    def load_yfinance(self, symbol: str, start: Optional[str], end: Optional[str], interval: str="1d") -> pd.DataFrame:
        import yfinance as yf
        df = yf.download(symbol, start=start, end=end, interval=interval, auto_adjust=True, progress=False)
        if df is None or df.empty:
            raise ValueError("yfinance returned empty DataFrame")
        df = _normalize_ohlcv(df)
        if not _validate_ohlc(df):
            raise ValueError("Data failed OHLC validation")
        df["symbol"] = symbol
        return df

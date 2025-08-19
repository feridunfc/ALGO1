from __future__ import annotations
import pandas as pd
import numpy as np

def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = ["_".join([str(c) for c in col if c is not None]).lower() for col in df.columns]
    else:
        df.columns = [str(c).lower() for c in df.columns]

    mapping = {"adj close": "adj_close", "adj_close": "adj_close"}
    df = df.rename(columns=mapping)

    if "close" not in df.columns and "adj_close" in df.columns:
        df["close"] = df["adj_close"]

    required = ["open", "high", "low", "close"]
    for col in required:
        if col not in df.columns:
            raise ValueError("yfinance returned unexpected columns")
    if "volume" not in df.columns:
        df["volume"] = np.nan

    for c in ["open", "high", "low", "close", "volume"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    return df

def validate_ohlc(df: pd.DataFrame) -> bool:
    required = ['open','high','low','close','volume']
    if not all(col in df.columns for col in required):
        return False
    if (df['high'] < df['low']).any():
        return False
    if (df['close'] > df['high']).any() or (df['close'] < df['low']).any():
        return False
    return True

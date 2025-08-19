
from __future__ import annotations
from typing import Any, Iterable, List, Optional, Sequence, Union
import pandas as pd
import numpy as np

OHLCV_COLS = ["timestamp","open","high","low","close","volume"]

def _from_ccxt_list(rows: Sequence[Sequence[Any]]) -> pd.DataFrame:
    # ccxt: [ms, o, h, l, c, v]
    arr = np.asarray(rows, dtype=object)
    if arr.ndim != 2 or arr.shape[1] < 6:
        return pd.DataFrame(columns=OHLCV_COLS)
    df = pd.DataFrame(arr[:, :6], columns=["timestamp","open","high","low","close","volume"])
    return df

def _from_dicts(rows: Iterable[dict]) -> pd.DataFrame:
    tmp = list(rows)
    if not tmp:
        return pd.DataFrame(columns=OHLCV_COLS)
    # allow short keys t,o,h,l,c,v
    key_map = {
        "t":"timestamp","time":"timestamp","timestamp":"timestamp","date":"timestamp",
        "o":"open","open":"open",
        "h":"high","high":"high",
        "l":"low","low":"low",
        "c":"close","close":"close","adj_close":"close","adj close":"close",
        "v":"volume","vol":"volume","volume":"volume"
    }
    norm = []
    for r in tmp:
        nr = {}
        for k,v in r.items():
            nk = key_map.get(str(k).lower().strip())
            if nk:
                nr[nk] = v
        norm.append(nr)
    return pd.DataFrame(norm)

def _from_yf_multiindex(df: pd.DataFrame) -> pd.DataFrame:
    # yfinance two-level columns either (OHLCV x Tickers) or (Tickers x OHLCV)
    lvl0 = [str(x).lower() for x in df.columns.get_level_values(0)]
    ohlc_set = {"open","high","low","close","adj close","adj_close","volume"}
    if set(lvl0) & ohlc_set:
        # Level0: OHLCV, Level1: tickers
        out = df.stack(level=1).rename_axis(["timestamp","symbol"]).reset_index()
    else:
        # Level0: tickers, Level1: OHLCV
        out = df.stack(level=0).rename_axis(["timestamp","symbol"]).reset_index()
    out.columns = [str(c).lower().replace(" ", "_") for c in out.columns]
    if "adj_close" in out.columns:
        out["close"] = out["adj_close"]
    keep = ["timestamp","symbol","open","high","low","close","volume"]
    out = out[keep]
    return out

def normalize_ohlcv(
    data: Union[pd.DataFrame, Iterable[dict], Sequence[Sequence[Any]]],
    source: str = "generic",
    symbol: Optional[str] = None,
    timeframe: Optional[str] = None,
) -> pd.DataFrame:
    """Normalize various OHLCV inputs into a standard dataframe.

    Output columns: timestamp (UTC tz-aware), [symbol], open, high, low, close, volume
    """
    if isinstance(data, pd.DataFrame):
        df = data.copy()
        if isinstance(df.columns, pd.MultiIndex):
            df = _from_yf_multiindex(df)
        else:
            # Try to align single-level columns
            col_map = {
                "date":"timestamp","time":"timestamp","t":"timestamp","timestamp":"timestamp",
                "o":"open","open":"open",
                "h":"high","high":"high",
                "l":"low","low":"low",
                "c":"close","close":"close","adj_close":"close","adj close":"close",
                "v":"volume","vol":"volume","volume":"volume"
            }
            df.columns = [col_map.get(str(c).lower().strip(), str(c).lower().strip()) for c in df.columns]
            # Add symbol if multi-ticker absent
            if "symbol" not in df.columns and symbol is not None:
                df["symbol"] = symbol
            # Reorder if possible
            keep = ["timestamp"] + (["symbol"] if "symbol" in df.columns else []) + ["open","high","low","close","volume"]
            df = df[[c for c in keep if c in df.columns]]
    elif isinstance(data, (list, tuple)) and data and isinstance(data[0], (list, tuple)):
        df = _from_ccxt_list(data)  # list of lists
        if symbol is not None:
            df["symbol"] = symbol
    else:
        df = _from_dicts(data)  # iterable of dicts
        if symbol is not None and "symbol" not in df.columns:
            df["symbol"] = symbol

    # dtype & tz
    if "timestamp" in df.columns:
        unit = "ms" if source.lower() in {"ccxt","binance","bybit"} else None
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit=unit, utc=True, errors="coerce")
    df = df.dropna(subset=["timestamp"]).copy()

    # ensure numeric
    for c in ["open","high","low","close","volume"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.dropna(subset=["open","high","low","close"]).copy()

    # select & order
    cols = ["timestamp"] + (["symbol"] if "symbol" in df.columns else []) + ["open","high","low","close","volume"]
    df = df[cols].sort_values("timestamp").reset_index(drop=True)

    # remove duplicates
    subset = ["timestamp"] + (["symbol"] if "symbol" in df.columns else [])
    df = df.drop_duplicates(subset=subset, keep="last").reset_index(drop=True)
    return df

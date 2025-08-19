
from __future__ import annotations
from typing import Dict, Any
import pandas as pd
import numpy as np
from data_layer.indicators import sma, rsi

def build_features(df: pd.DataFrame, spec: Dict[str, Any] | None = None) -> pd.DataFrame:
    """Given a per-symbol OHLCV dataframe, append feature columns.
    Expected columns: timestamp, [symbol], open, high, low, close, volume
    """
    if df.empty:
        return df
    out = df.copy()

    # Basic returns
    out["ret_1"] = out["close"].pct_change()
    out["ret_5"] = out["close"].pct_change(5)
    out["hl_spread"] = (out["high"] - out["low"]) / out["close"]
    out["range_pct"] = (out["high"] - out["low"]) / out["low"].replace(0, np.nan)

    # Indicators spec
    spec = spec or {"indicators":[{"name":"sma_20","kind":"sma","window":20},{"name":"sma_50","kind":"sma","window":50},{"name":"rsi_14","kind":"rsi","window":14}]}
    for ind in spec.get("indicators", []):
        name = ind.get("name")
        kind = ind.get("kind")
        win  = int(ind.get("window", 14))
        if kind == "sma":
            out[name] = sma(out["close"], win)
        elif kind == "rsi":
            out[name] = rsi(out["close"], win)
        else:
            # unknown -> skip
            pass

    return out

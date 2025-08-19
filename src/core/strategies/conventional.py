from __future__ import annotations
import pandas as pd
import numpy as np

def _sma(s: pd.Series, n: int) -> pd.Series:
    n = max(int(n), 1)
    return pd.Series(s, dtype=float).rolling(n).mean()

def _rsi(close: pd.Series, n: int = 14) -> pd.Series:
    close = pd.Series(close, dtype=float)
    delta = close.diff()
    up = delta.clip(lower=0).ewm(alpha=1.0/n, adjust=False).mean()
    down = (-delta.clip(upper=0)).ewm(alpha=1.0/n, adjust=False).mean()
    rs = up / (down + 1e-12)
    return 100 - 100/(1 + rs)

def ma_crossover(df: pd.DataFrame, params: dict) -> pd.Series:
    """Basit uzun/çık sinyali: fast SMA > slow SMA => 1, değilse 0."""
    fast = int(params.get("ma_fast", 10))
    slow = int(params.get("ma_slow", 30))
    c = pd.Series(df["close"], dtype=float)
    f = _sma(c, fast)
    s = _sma(c, slow)
    sig = (f > s).astype(int)
    return sig.fillna(0)

def bb_mean_reversion(df: pd.DataFrame, params: dict) -> pd.Series:
    """BB orta çizgisinin altına inince uzun, üstüne çıkınca çık (basit MR)."""
    w = int(params.get("bb_window", 20))
    k = float(params.get("bb_k", 2.0))
    c = pd.Series(df["close"], dtype=float)
    m = c.rolling(w).mean()
    sd = c.rolling(w).std(ddof=0)
    lower = m - k*sd
    upper = m + k*sd

    # Basit histerezis: alt banda altına inince gir, üst banda üstüne çıkınca çık
    sig = pd.Series(0, index=df.index, dtype=int)
    in_pos = False
    for i in range(len(df)):
        px = c.iat[i]
        lo = lower.iat[i] if not np.isnan(lower.iat[i]) else None
        up = upper.iat[i] if not np.isnan(upper.iat[i]) else None
        if lo is None or up is None:
            sig.iat[i] = sig.iat[i-1] if i>0 else 0
            continue
        if not in_pos and px < lo:
            in_pos = True
        elif in_pos and px > up:
            in_pos = False
        sig.iat[i] = 1 if in_pos else 0
    return sig

def rsi_reversion(df: pd.DataFrame, params: dict) -> pd.Series:
    """RSI < buy ile gir, RSI > sell ile çık (histerezis)."""
    n = int(params.get("rsi_window", 14))
    buy = float(params.get("rsi_buy", 30))
    sell = float(params.get("rsi_sell", 50))
    r = _rsi(df["close"], n)

    sig = pd.Series(0, index=df.index, dtype=int)
    in_pos = False
    for i in range(len(df)):
        rv = r.iat[i]
        if np.isnan(rv):
            sig.iat[i] = sig.iat[i-1] if i>0 else 0
            continue
        if not in_pos and rv < buy:
            in_pos = True
        elif in_pos and rv > sell:
            in_pos = False
        sig.iat[i] = 1 if in_pos else 0
    return sig

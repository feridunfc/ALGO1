from __future__ import annotations
import pandas as pd
import numpy as np

def _rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    up = (delta.clip(lower=0)).ewm(alpha=1/period, adjust=False).mean()
    down = (-delta.clip(upper=0)).ewm(alpha=1/period, adjust=False).mean()
    rs = up / down.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return rsi

def _atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    h, l, c = df['high'], df['low'], df['close']
    tr = pd.concat([(h - l), (h - c.shift(1)).abs(), (l - c.shift(1)).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1/period, adjust=False).mean()

def build_features(df: pd.DataFrame, ma_fast: int = 10, ma_slow: int = 30) -> pd.DataFrame:
    """Leakage-free TA features; **all shifted by 1** relative to target.

    Returns a DataFrame aligned to df.index with NaNs dropped at the end.
    """
    out = pd.DataFrame(index=df.index)
    out['ret_1'] = df['close'].pct_change().shift(1)
    out['ma_fast'] = df['close'].rolling(ma_fast).mean().shift(1)
    out['ma_slow'] = df['close'].rolling(ma_slow).mean().shift(1)
    out['rsi'] = _rsi(df['close']).shift(1)
    out['atr'] = _atr(df).shift(1)
    out['vol'] = df['close'].pct_change().rolling(20).std().shift(1)
    out = out.dropna()
    return out

def build_target(df: pd.DataFrame, horizon: int = 1, classification: bool = True) -> pd.Series:
    fwd = df['close'].pct_change(horizon).shift(-horizon)
    if classification:
        y = (fwd > 0).astype(int)  # 1 if up
    else:
        y = fwd
    y = y.reindex(df.index).dropna()
    # Align y to features index later (intersection)
    return y
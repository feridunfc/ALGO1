from __future__ import annotations
import numpy as np, pandas as pd

def atr(df: pd.DataFrame, window: int = 14) -> pd.Series:
    h, l, c = df["high"], df["low"], df["close"]
    tr = pd.concat([(h-l), (h-c.shift()).abs(), (l-c.shift()).abs()], axis=1).max(axis=1)
    return tr.rolling(window).mean()

def apply_vol_target(signal: pd.Series, ret: pd.Series, target_ann: float) -> pd.Series:
    rolling_vol = ret.rolling(20).std().fillna(method="bfill")
    ann_vol = rolling_vol * np.sqrt(252)
    scale = target_ann / (ann_vol.replace(0, np.nan))
    scale = scale.clip(upper=1.0).fillna(0.0)
    return (signal.fillna(0.0) * scale).clip(-1.0, 1.0)

def apply_basic_stops(df: pd.DataFrame, position: pd.Series, atr_window: int, stop_mult: float) -> pd.Series:
    a = atr(df, atr_window).fillna(method="bfill")
    rng = (df["high"] - df["low"]).fillna(0.0)
    breach = (rng > stop_mult * a).astype(float)
    flat = position.copy()
    flat[breach > 0] = 0.0
    return flat

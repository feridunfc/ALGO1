from __future__ import annotations
import numpy as np, pandas as pd

def rsi(series: pd.Series, window: int = 14) -> pd.Series:
    delta = series.diff()
    gain = (delta.clip(lower=0)).ewm(alpha=1/window, adjust=False).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1/window, adjust=False).mean()
    rs = gain / (loss + 1e-12)
    return 100 - (100 / (1 + rs))

def realized_vol(ret: pd.Series, window: int = 20) -> pd.Series:
    return ret.rolling(window).std() * np.sqrt(252)

def make_basic_features(df: pd.DataFrame) -> pd.DataFrame:
    c = df["close"]
    feats = pd.DataFrame(index=df.index)
    feats["ret1"] = c.pct_change().fillna(0.0)
    feats["ret5"] = c.pct_change(5).fillna(0.0)
    feats["rsi14"] = rsi(c, 14).fillna(method="bfill").fillna(50.0)
    feats["sma10"] = c.rolling(10).mean().pct_change().fillna(0.0)
    feats["sma50"] = c.rolling(50).mean().pct_change().fillna(0.0)
    feats["vol20"] = realized_vol(feats["ret1"], 20).fillna(method="bfill").fillna(0.0)
    y = (c.pct_change().shift(-1) > 0).astype(int)
    return feats, y

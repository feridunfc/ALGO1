from __future__ import annotations
import numpy as np, pandas as pd

def ta_block(df: pd.DataFrame, ma_fast: int=20, ma_slow: int=50, rsi_window: int=14) -> pd.DataFrame:
    out = df.copy()
    close = out["close"].astype(float)
    out["ma_fast"] = close.rolling(ma_fast).mean()
    out["ma_slow"] = close.rolling(ma_slow).mean()
    delta = close.diff()
    up = np.where(delta>0, delta, 0.0)
    down = np.where(delta<0, -delta, 0.0)
    roll_up = pd.Series(up, index=out.index).rolling(rsi_window).mean()
    roll_down = pd.Series(down, index=out.index).rolling(rsi_window).mean()
    rs = roll_up / (roll_down.replace(0, np.nan))
    out["rsi"] = 100 - (100/(1+rs))
    return out

def regime_block(df: pd.DataFrame, vol_lb: int=30) -> pd.DataFrame:
    out = df.copy()
    ret = out["close"].pct_change()
    out["vol"] = ret.rolling(vol_lb).std()
    out["ret_63"] = out["close"].pct_change(63)
    med_vol = out["vol"].rolling(252).median()
    out["regime_bull"] = ((out["ret_63"]>0) & (out["vol"]<=med_vol)).astype(int)
    return out

def anomaly_block(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    z = (out["close"].pct_change().fillna(0)).rolling(20).apply(lambda s: (s - s.mean()).abs().sum(), raw=False)
    z = (z - z.min())/(z.max()-z.min() + 1e-9)
    out["anomaly_score"] = z.fillna(0.5)
    return out

def make_features(df: pd.DataFrame) -> pd.DataFrame:
    x = ta_block(df)
    x = regime_block(x)
    x = anomaly_block(x)
    return x


import numpy as np
import pandas as pd

def compute_market_regime(df: pd.DataFrame, ret_col: str = "close", vol_lookback: int = 60) -> pd.Series:
    px = df[ret_col].astype(float)
    ma_fast = px.rolling(50).mean()
    ma_slow = px.rolling(200).mean()
    trend = np.sign(ma_fast - ma_slow).fillna(0.0)
    vol = px.pct_change().rolling(vol_lookback).std()
    vol_z = (vol - vol.rolling(vol_lookback).mean()) / (vol.rolling(vol_lookback).std() + 1e-9)
    inv_vol = 1.0 / (1.0 + vol_z.clip(lower=-3, upper=3) + 3)
    regime = (trend * inv_vol).clip(-1, 1)
    regime.name = "regime_score"
    return regime

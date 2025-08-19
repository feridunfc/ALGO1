import numpy as np
import pandas as pd

def validate_ohlc(df: pd.DataFrame) -> bool:
    required = ['open','high','low','close','volume']
    if not all(c in df.columns for c in required):
        return False
    if (df['high'] < df['low']).any():
        return False
    if (df['close'] > df['high']).any() or (df['close'] < df['low']).any():
        return False
    return True

def add_basic_indicators(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out['ret1'] = out['close'].pct_change().fillna(0.0)
    out['sma_10'] = out['close'].rolling(10).mean().ffill()
    out['sma_50'] = out['close'].rolling(50).mean().ffill()
    out['rsi_14'] = _rsi(out['close'], 14)
    out['vol_20'] = out['ret1'].rolling(20).std(ddof=0).ffill()
    return out

def _rsi(series: pd.Series, n: int = 14) -> pd.Series:
    delta = series.diff()
    gain = (delta.where(delta > 0, 0.0)).rolling(n).mean()
    loss = (-delta.where(delta < 0, 0.0)).rolling(n).mean()
    rs = gain / (loss + 1e-12)
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(50.0)

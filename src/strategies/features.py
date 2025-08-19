import pandas as pd
import numpy as np

def make_basic_features(df: pd.DataFrame) -> pd.DataFrame:
    r1 = df["close"].pct_change().fillna(0)
    r5 = df["close"].pct_change(5).fillna(0)
    r10 = df["close"].pct_change(10).fillna(0)
    ma10 = df["close"].rolling(10, min_periods=10).mean()
    ma20 = df["close"].rolling(20, min_periods=20).mean()
    ma50 = df["close"].rolling(50, min_periods=50).mean()
    vol20 = df["close"].pct_change().rolling(20, min_periods=20).std(ddof=0)
    hi20 = df["high"].rolling(20, min_periods=20).max()
    lo20 = df["low"].rolling(20, min_periods=20).min()
    bb_mid = ma20
    bb_up = ma20 + 2*df["close"].rolling(20, min_periods=20).std(ddof=0)
    bb_dn = ma20 - 2*df["close"].rolling(20, min_periods=20).std(ddof=0)
    k = (df["close"] - lo20) / (hi20 - lo20 + 1e-12)
    x = pd.DataFrame({
        "r1": r1, "r5": r5, "r10": r10,
        "ma10": ma10, "ma20": ma20, "ma50": ma50,
        "ma_spread": (ma10 - ma20) / (ma20 + 1e-12),
        "vol20": vol20,
        "ch20": (df["close"]-lo20)/(hi20-lo20+1e-12),
        "bb_pos": (df["close"]-bb_mid)/(bb_up-bb_dn+1e-12),
        "k_stoch": k
    })
    return x.fillna(0.0)

def target_next_up(df: pd.DataFrame) -> pd.Series:
    return (df["close"].pct_change().shift(-1) > 0).astype(int)

# TA helpers
def rsi(series: pd.Series, n: int = 14) -> pd.Series:
    delta = series.diff()
    up = (delta.clip(lower=0)).rolling(n, min_periods=n).mean()
    down = (-delta.clip(upper=0)).rolling(n, min_periods=n).mean()
    rs = up / (down + 1e-12)
    return 100 - (100/(1+rs))

def ema(series: pd.Series, n: int) -> pd.Series:
    return series.ewm(span=n, adjust=False).mean()

def macd(series: pd.Series, fast=12, slow=26, signal=9):
    macd_line = ema(series, fast) - ema(series, slow)
    signal_line = ema(macd_line, signal)
    hist = macd_line - signal_line
    return macd_line, signal_line, hist)

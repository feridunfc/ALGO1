# src/strategies/features.py
"""
Compatibility shim for legacy strategies importing `src.strategies.features`.
Lightweight indicators + label helpers (dependency-free).
"""
from __future__ import annotations
import numpy as np
import pandas as pd

# import pandas as pd
# import numpy as np

def target_next_up(df: pd.DataFrame, col: str = "close", horizon: int = 1):
    s = df[col].pct_change(horizon).shift(-horizon)
    y = (s > 0).astype(int)
    return y, s

def make_basic_features(df: pd.DataFrame):
    out = pd.DataFrame(index=df.index)
    if "close" in df:
        out["ret1"] = df["close"].pct_change().fillna(0.0)
        out["ret5"] = df["close"].pct_change(5).fillna(0.0)
        out["vol10"] = df["close"].pct_change().rolling(10).std().fillna(0.0)
    return out

def build_features(df: pd.DataFrame):
    # Eski kodların çağırdığı olası isim
    return make_basic_features(df)


# ---------- utils ----------
def _s(x) -> pd.Series:
    return x if isinstance(x, pd.Series) else pd.Series(x)

# ---------- indicators ----------
def rsi(close: pd.Series, period: int = 14) -> pd.Series:
    c = _s(close).astype(float)
    d = c.diff()
    up = d.clip(lower=0.0)
    dn = (-d.clip(upper=0.0))
    roll_up = up.ewm(alpha=1/period, adjust=False).mean()
    roll_dn = dn.ewm(alpha=1/period, adjust=False).mean().replace(0, np.nan)
    rs = roll_up / roll_dn
    out = 100 - (100 / (1 + rs))
    return out.fillna(50.0)

def macd(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    c = _s(close).astype(float)
    ema_f = c.ewm(span=fast, adjust=False).mean()
    ema_s = c.ewm(span=slow, adjust=False).mean()
    line = ema_f - ema_s
    sig  = line.ewm(span=signal, adjust=False).mean()
    hist = line - sig
    return line, sig, hist

def bollinger_bands(close: pd.Series, window: int = 20, n_std: float = 2.0):
    c = _s(close).astype(float)
    ma = c.rolling(window).mean()
    sd = c.rolling(window).std()
    up = ma + n_std * sd
    lo = ma - n_std * sd
    return up, ma, lo

def stochastic_kd(high: pd.Series, low: pd.Series, close: pd.Series,
                  k_period: int = 14, d_period: int = 3):
    h, l, c = _s(high).astype(float), _s(low).astype(float), _s(close).astype(float)
    ll = l.rolling(k_period).min()
    hh = h.rolling(k_period).max().replace(0, np.nan)
    k = 100 * (c - ll) / (hh - ll)
    d = k.rolling(d_period).mean()
    return k.fillna(50.0), d.fillna(50.0)

def atr(high: pd.Series, low: pd.Series, close: pd.Series, window: int = 14) -> pd.Series:
    h, l, c = _s(high), _s(low), _s(close)
    pc = c.shift(1)
    tr = pd.concat([(h - l), (h - pc).abs(), (l - pc).abs()], axis=1).max(axis=1)
    return tr.rolling(window).mean().bfill()

def donchian_channels(high: pd.Series, low: pd.Series, window: int = 20):
    h, l = _s(high), _s(low)
    up = h.rolling(window).max()
    lo = l.rolling(window).min()
    mid = (up + lo) / 2.0
    return up, mid, lo

def adx(high: pd.Series, low: pd.Series, close: pd.Series, window: int = 14) -> pd.Series:
    h, l, c = _s(high).astype(float), _s(low).astype(float), _s(close).astype(float)
    plus_dm = (h.diff()).clip(lower=0.0)
    minus_dm = (-l.diff()).clip(lower=0.0)
    tr = atr(h, l, c, window=1).replace(0, np.nan)
    plus_di = 100 * (plus_dm.ewm(alpha=1/window, adjust=False).mean() / tr)
    minus_di = 100 * (minus_dm.ewm(alpha=1/window, adjust=False).mean() / tr)
    dx = (abs(plus_di - minus_di) / (plus_di + minus_di)).replace([np.inf, -np.inf], np.nan) * 100
    return dx.ewm(alpha=1/window, adjust=False).mean().fillna(20.0)

# ---------- basic feature set ----------
def compute_basic_features(df: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame(index=df.index)
    if "close" in df:
        c = pd.Series(df["close"]).astype(float)
        out["ret_1"] = c.pct_change().fillna(0.0)
        out["ma_10"] = c.rolling(10).mean().bfill()
        out["ma_20"] = c.rolling(20).mean().bfill()
        out["vol_10"] = c.pct_change().rolling(10).std().bfill().fillna(0.0)
    return out

# # ---------- LABEL HELPERS (legacy names dahil) ----------
# def target_next_up(close: pd.Series, horizon: int = 1) -> pd.Series:
#     """Binary 0/1: next close > current close"""
#     c = _s(close).astype(float)
#     return (c.shift(-horizon) > c).astype(int)

def target_next_down(close: pd.Series, horizon: int = 1) -> pd.Series:
    """Binary 0/1: next close < current close"""
    c = _s(close).astype(float)
    return (c.shift(-horizon) < c).astype(int)

def target_next_updown(close: pd.Series, horizon: int = 1) -> pd.Series:
    """Sign -1/+1: next up -> 1, next down -> -1 (eşitlik -> 0)"""
    c = _s(close).astype(float)
    nxt = c.shift(-horizon)
    sgn = np.sign((nxt - c).fillna(0.0))
    return sgn.astype(int)

def target_trinary(close: pd.Series, horizon: int = 1, threshold: float = 0.0) -> pd.Series:
    """-1/0/1: horizon getirisi threshold’tan büyükse 1, küçükse -1, değilse 0"""
    c = _s(close).astype(float)
    ret = (c.shift(-horizon) / c) - 1.0
    return pd.Series(np.where(ret > threshold, 1, np.where(ret < -threshold, -1, 0)), index=c.index).astype(int)

def make_labels(df: pd.DataFrame, horizon: int = 1, mode: str = "binary_up", threshold: float = 0.0) -> pd.Series:
    """Ortak etiket üretici"""
    if "close" not in df: raise KeyError("make_labels: 'close' kolonu gerekli")
    if mode == "binary_up":   return target_next_up(df["close"], horizon)
    if mode == "binary_down": return target_next_down(df["close"], horizon)
    if mode == "sign":        return target_next_updown(df["close"], horizon)
    if mode == "trinary":     return target_trinary(df["close"], horizon, threshold)
    raise ValueError(f"Unknown mode: {mode}")

# ---------- LEGACY ALIASES (import kırılmasın) ----------
make_basic_features   = compute_basic_features
make_features_basic   = compute_basic_features
make_features         = compute_basic_features
build_basic_features  = compute_basic_features

# bazı repolarda label fonksiyon isimleri farklı olabiliyor:
build_labels          = make_labels
compute_labels        = make_labels
make_target           = make_labels
target_binary         = target_next_up
target_next_binary    = target_next_up

__all__ = [
    # indicators
    "rsi","macd","bollinger_bands","stochastic_kd","atr","donchian_channels","adx",
    # features
    "compute_basic_features","make_basic_features","make_features_basic","make_features","build_basic_features",
    # labels
    "target_next_up","target_next_down","target_next_updown","target_trinary",
    "make_labels","build_labels","compute_labels","make_target","target_binary","target_next_binary",
]

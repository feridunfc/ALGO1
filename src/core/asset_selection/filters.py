
from __future__ import annotations
import pandas as pd
import numpy as np
from typing import List, Dict

def momentum_score(df: pd.DataFrame, lb: int = 20) -> float:
    if len(df) < lb + 1: 
        return np.nan
    return (df["close"].iloc[-1] / df["close"].iloc[-lb] - 1.0)

def volatility_score(df: pd.DataFrame, lb: int = 20) -> float:
    if len(df) < lb:
        return np.nan
    return -float(df["close"].pct_change().iloc[-lb:].std())  # düşük vol daha yüksek skor

def liquidity_score(df: pd.DataFrame, lb: int = 20) -> float:
    if "volume" not in df.columns or len(df) < lb:
        return np.nan
    return float(df["volume"].iloc[-lb:].mean())

def rank_assets(hist_map: Dict[str, pd.DataFrame], top_k: int = 5) -> List[str]:
    rows = []
    for sym, df in hist_map.items():
        m = momentum_score(df)
        v = volatility_score(df)
        l = liquidity_score(df)
        if not (np.isfinite(m) and np.isfinite(v) and np.isfinite(l)):
            continue
        # basit ağırlıklar: momentum 0.5, vol 0.2, likidite 0.3 (normalize edilmemiş örnek)
        score = 0.5*m + 0.2*v + 0.3*(l / (1.0 + l))  # likiditeyi [0,1) sıkıştır
        rows.append((sym, score))
    rows.sort(key=lambda x: x[1], reverse=True)
    return [sym for sym, _ in rows[:top_k]]

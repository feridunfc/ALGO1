from __future__ import annotations
import pandas as pd
import numpy as np

def generate_sma_crossover_signals(df: pd.DataFrame, fast: int, slow: int) -> pd.Series:
    sma_f = df["close"].rolling(fast).mean()
    sma_s = df["close"].rolling(slow).mean()
    sig = np.where(sma_f > sma_s, 1, -1)
    return pd.Series(sig, index=df.index, name="signal")

def generate_rsi_signals(df: pd.DataFrame, rsi_period: int, low: float=30.0, high: float=70.0) -> pd.Series:
    delta = df["close"].diff()
    gain = (delta.where(delta>0, 0)).rolling(rsi_period).mean()
    loss = (-delta.where(delta<0, 0)).rolling(rsi_period).mean()
    rs = gain/(loss.replace(0, np.nan))
    rsi = 100 - (100/(1+rs))
    sig = np.where(rsi < low, 1, np.where(rsi > high, -1, 0))
    sig = pd.Series(sig, index=df.index, name="signal").fillna(0)
    return sig

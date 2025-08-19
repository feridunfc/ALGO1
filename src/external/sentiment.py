
from __future__ import annotations
import pandas as pd, numpy as np

def fetch_sentiment_series(start, end, freq) -> pd.DataFrame:
    idx = pd.date_range(start=start, end=end, freq=freq, tz="UTC")
    s = np.random.randn(len(idx)) * 0.05
    return pd.DataFrame({"timestamp": idx, "sentiment": s})

def fetch_macro_series(start, end, freq) -> pd.DataFrame:
    idx = pd.date_range(start=start, end=end, freq=freq, tz="UTC")
    x = np.sin(np.linspace(0, 3.14, len(idx)))
    return pd.DataFrame({"timestamp": idx, "macro": x})

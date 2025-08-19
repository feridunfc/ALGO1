
import numpy as np
import pandas as pd

def anomaly_zscore(series: pd.Series, lookback: int = 60) -> pd.Series:
    mu = series.rolling(lookback).mean()
    sd = series.rolling(lookback).std()
    z = (series - mu) / (sd + 1e-9)
    score = np.tanh(np.abs(z) / 3)
    return score.rename("anomaly_score")

def compute_anomaly(df: pd.DataFrame, ret_col: str = "close", method: str = "zscore") -> pd.Series:
    rets = df[ret_col].pct_change().fillna(0.0)
    if method == "zscore":
        return anomaly_zscore(rets)
    try:
        from sklearn.ensemble import IsolationForest
        X = rets.to_frame("r").fillna(0.0).values
        iso = IsolationForest(n_estimators=100, contamination=0.02, random_state=42)
        s = -iso.fit_predict(X)
        s = pd.Series(s, index=rets.index).rolling(5).mean().fillna(0.0)
        return s.rename("anomaly_score")
    except Exception:
        return anomaly_zscore(rets)

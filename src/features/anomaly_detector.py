import pandas as pd
def anomaly_score(close: pd.Series, lookback:int=50)->pd.Series:
    z = (close - close.rolling(lookback).mean()) / (close.rolling(lookback).std()+1e-9)
    return z.clip(-5,5).abs()

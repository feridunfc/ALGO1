import pandas as pd, numpy as np
def regime_flags(close: pd.Series)->pd.DataFrame:
    rets = close.pct_change()
    vol = rets.rolling(30).std()
    trend = close.rolling(50).mean() - close.rolling(200).mean()
    return pd.DataFrame({'trend_up': (trend>0).astype(int), 'high_vol': (vol > vol.rolling(252).quantile(0.7)).astype(int)}, index=close.index)

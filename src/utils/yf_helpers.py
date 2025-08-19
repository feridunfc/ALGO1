
# utils/yf_helpers.py
import pandas as pd

def normalize_yf(df: pd.DataFrame) -> pd.DataFrame:
    """Return df with columns: open, high, low, close, volume (lowercase)."""
    if df is None or df.empty:
        return pd.DataFrame()
    # Support multi-index columns from yfinance
    if isinstance(df.columns, pd.MultiIndex):
        # Typical yfinance structure ('Open','High','Low','Close','Adj Close','Volume')
        df = df.copy()
        df.columns = [c[0].lower() for c in df.columns]
    else:
        df = df.copy()
        df.columns = [c.lower() for c in df.columns]

    # Map variations
    mapping = {}
    cols = set(df.columns)
    for want in ["open","high","low","close","volume"]:
        if want in cols:
            mapping[want] = want
        elif want.capitalize() in cols:
            mapping[want.capitalize()] = want
        elif want.upper() in cols:
            mapping[want.upper()] = want

    df = df.rename(columns=mapping)
    # Keep only needed columns if present
    keep = [c for c in ["open","high","low","close","volume"] if c in df.columns]
    return df[keep].dropna(how="any")

def synthetic_walk(symbol: str, n: int = 1000, start_price: float = 100.0, seed: int = 42):
    import numpy as np
    import pandas as pd
    rng = np.random.default_rng(seed)
    rets = rng.normal(0, 0.001, n)
    price = start_price * (1 + rets).cumprod()
    idx = pd.date_range("2018-01-01", periods=n, freq="D")
    df = pd.DataFrame({
        "open": price * (1 + rng.normal(0, 0.0005, n)),
        "high": price * (1 + rng.normal(0.001, 0.0005, n)),
        "low":  price * (1 + rng.normal(-0.001, 0.0005, n)),
        "close": price,
        "volume": rng.integers(1000, 5000, n)
    }, index=idx)
    return df

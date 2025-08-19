
import pandas as pd

def apply_split(df: pd.DataFrame, split_date: pd.Timestamp, ratio: float) -> pd.DataFrame:
    # Apply split by multiplying price columns prior to split_date by ratio and dividing volume.
    cols = {c: c.lower() for c in df.columns}
    dfn = df.rename(columns=cols).copy()
    pre = dfn.index < split_date
    for c in ["open","high","low","close"]:
        if c in dfn.columns:
            dfn.loc[pre, c] = dfn.loc[pre, c] * ratio
    if "volume" in dfn.columns:
        dfn.loc[pre, "volume"] = dfn.loc[pre, "volume"] / ratio
    return dfn

def apply_dividend(df: pd.DataFrame, ex_date: pd.Timestamp, amount: float) -> pd.DataFrame:
    # Simple dividend adjustment: subtract amount from pre ex-date close (research-only).
    cols = {c: c.lower() for c in df.columns}
    dfn = df.rename(columns=cols).copy()
    pre = dfn.index < ex_date
    if "close" in dfn.columns:
        dfn.loc[pre, "close"] = dfn.loc[pre, "close"] - amount
    return dfn

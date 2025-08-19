from __future__ import annotations
import pandas as pd

def validate_data(df: pd.DataFrame) -> dict:
    out = {
        "rows": len(df),
        "cols": len(df.columns),
        "missing_pct": float(df.isna().mean().mean()),
        "stale_rows": int((df.index.to_series().diff().dt.total_seconds() > 7*24*3600).sum())
            if isinstance(df.index, pd.DatetimeIndex) else 0,
    }
    num = df.select_dtypes("number")
    if not num.empty:
        q1 = num.quantile(0.25); q3 = num.quantile(0.75); iqr = (q3 - q1)
        mask = (num.lt(q1 - 3*iqr)) | (num.gt(q3 + 3*iqr))
        out["outlier_count"] = int(mask.sum().sum())
    else:
        out["outlier_count"] = 0
    return out

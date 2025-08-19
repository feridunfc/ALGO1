
from __future__ import annotations
import pandas as pd

def data_quality_report(df: pd.DataFrame) -> dict:
    report = {
        "rows": int(len(df)),
        "missing_any": int(df.isna().any(axis=1).sum()),
        "duplicates": 0,
        "non_monotonic_time": 0,
        "negative_prices": 0,
    }
    if "timestamp" in df.columns:
        subset = ["timestamp"] + (["symbol"] if "symbol" in df.columns else [])
        report["duplicates"] = int(df.duplicated(subset=subset).sum())
        if not df["timestamp"].is_monotonic_increasing:
            report["non_monotonic_time"] = 1
    for c in ["open","high","low","close"]:
        if c in df.columns:
            report["negative_prices"] += int((df[c] < 0).sum())
    return report

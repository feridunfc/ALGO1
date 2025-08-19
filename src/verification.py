
import os
import pandas as pd
from .data.validation import OHLCValidator, normalize_ohlc_columns
from .engines.metrics_engine import MetricsEngine
import numpy as np

def verify_all(repo_root: str) -> dict:
    report = {"data_quality": None, "metrics_example": None}
    sample_csv = None
    for root, _, files in os.walk(repo_root):
        for f in files:
            if f.endswith(".csv"):
                sample_csv = os.path.join(root, f)
                break
        if sample_csv:
            break
    if sample_csv:
        try:
            df = pd.read_csv(sample_csv)
            if "date" in df.columns:
                df["date"] = pd.to_datetime(df["date"])
                df = df.set_index("date")
            df = normalize_ohlc_columns(df)
            report["data_quality"] = OHLCValidator().validate(df)
        except Exception as e:
            report["data_quality"] = f"error: {e}"
    else:
        report["data_quality"] = "no csv sample found"

    n = 252
    eq = pd.Series(1.0 + np.cumsum(np.random.normal(0.0003, 0.01, n)))
    eq = (1 + eq.pct_change().fillna(0)).cumprod()
    report["metrics_example"] = MetricsEngine.compute_all(eq / eq.iloc[0])
    return report

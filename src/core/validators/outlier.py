# src/core/validators/outlier.py
import pandas as pd
import numpy as np
from dataclasses import dataclass

@dataclass
class OutlierDetector:
    method: str = "iqr"
    threshold: float = 3.0   # IQR multiplier
    max_frac: float = 0.05   # max tolerated outlier fraction

    def validate(self, df: pd.DataFrame) -> None:
        cols = ["open","high","low","close"]
        x = df[cols].astype(float)
        if self.method == "iqr":
            q1 = x.quantile(0.25)
            q3 = x.quantile(0.75)
            iqr = q3 - q1
            lo = q1 - self.threshold * iqr
            hi = q3 + self.threshold * iqr
            mask = (x.lt(lo) | x.gt(hi)).any(axis=1)
            frac = float(mask.mean())
            # We don't mutate; just guard egregious cases
            if frac > self.max_frac:
                raise ValueError(f"OutlierDetector: outlier fraction {frac:.3f} > max {self.max_frac:.3f}")
        else:
            # fallback: zscore
            z = (x - x.mean()) / (x.std(ddof=0) + 1e-12)
            mask = (np.abs(z) > self.threshold).any(axis=1)
            frac = float(mask.mean())
            if frac > self.max_frac:
                raise ValueError(f"OutlierDetector(z): outlier fraction {frac:.3f} > max {self.max_frac:.3f}")

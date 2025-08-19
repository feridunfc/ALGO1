
import numpy as np
import pandas as pd

def psi(expected: pd.Series, actual: pd.Series, buckets: int = 10) -> float:
    """Population Stability Index between two distributions."""
    e, a = expected.dropna(), actual.dropna()
    if len(e) == 0 or len(a) == 0: return 0.0
    q = np.linspace(0, 1, buckets+1)
    cuts = e.quantile(q).values
    cuts[0], cuts[-1] = -np.inf, np.inf
    e_counts, _ = np.histogram(e, bins=cuts)
    a_counts, _ = np.histogram(a, bins=cuts)
    e_prop = np.clip(e_counts / e_counts.sum(), 1e-6, 1.0)
    a_prop = np.clip(a_counts / a_counts.sum(), 1e-6, 1.0)
    return float(((a_prop - e_prop) * np.log(a_prop / e_prop)).sum())

class DriftGuard:
    def __init__(self, threshold: float = 0.2):
        self.threshold = threshold
        self.reference = None

    def set_reference(self, series: pd.Series):
        self.reference = series.dropna().copy()

    def is_drift(self, series: pd.Series) -> bool:
        if self.reference is None: return False
        score = psi(self.reference, series)
        return bool(score >= self.threshold)

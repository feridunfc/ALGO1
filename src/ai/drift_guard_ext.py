from __future__ import annotations
import numpy as np
import pandas as pd

def _psi(expected: pd.Series, actual: pd.Series, buckets: int = 10) -> float:
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
    """
    Opsiyonel alibi_detect.KSDrift, yoksa PSI fallback.
    """
    def __init__(self, p_val: float = 0.05, psi_threshold: float = 0.2):
        self.detector = None
        try:
            from alibi_detect.cd import KSDrift
            self._KS = KSDrift
        except Exception:
            self._KS = None
        self.p_val = p_val
        self.psi_threshold = psi_threshold
        self._ref = None

    def set_reference(self, X_ref: np.ndarray):
        self._ref = X_ref
        if self._KS is not None:
            self.detector = self._KS(X_ref, p_val=self.p_val)

    def is_drift(self, X_new: np.ndarray) -> bool:
        if self._KS is not None and self.detector is not None:
            res = self.detector.predict(X_new)
            return bool(res.get("data", {}).get("is_drift", 0) == 1)
        if self._ref is None or self._ref.size == 0 or X_new.size == 0:
            return False
        return _psi(pd.Series(self._ref[:,0]), pd.Series(X_new[:,0])) >= self.psi_threshold

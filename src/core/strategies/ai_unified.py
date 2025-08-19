from __future__ import annotations
import numpy as np
import pandas as pd
from typing import Dict, Any, Optional
from core.models.registry import get_model, list_models

class AIUnifiedStrategy:
    """Model-agnostic strategy that maps proba -> signal (-1/0/1)."""
    def __init__(self, model_name: str, threshold: float = 0.5, model_params: Optional[Dict[str, Any]] = None):
        if model_name not in list_models():
            raise KeyError(f"Unknown model '{model_name}'. Available: {list_models()}")
        self.model = get_model(model_name, **(model_params or {}))
        self.threshold = float(threshold)

    def fit(self, X: pd.DataFrame, y: pd.Series, X_val: Optional[pd.DataFrame] = None, y_val: Optional[pd.Series] = None):
        eval_set = None
        if X_val is not None and y_val is not None:
            eval_set = [(X_val, y_val)]
        self.model.fit(X, y, eval_set=eval_set)

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        return self.model.predict_proba(X)

    def signals_from_proba(self, proba: np.ndarray) -> np.ndarray:
        """Assume binary classes {0,1}. Map to -1/0/1 via threshold and neutrality band."""
        if proba.ndim == 2 and proba.shape[1] >= 2:
            long_p = proba[:, 1]
        else:
            raise ValueError("Expected predict_proba with 2 columns (class 0/1)")
        # Neutral band around threshold ±0.05
        long_sig = (long_p >= self.threshold + 0.05).astype(int) - (long_p <= self.threshold - 0.05).astype(int)
        return long_sig  # -1, 0, +1

    def fit_predict_vectorized(self, df_features: pd.DataFrame, target: pd.Series, val_size: int = 0):
        """Leakage-free vectorized training + prediction (single split at end).

        For WF you should use walk_forward runner.

        Returns proba and signals aligned to index.
        """
        n = len(df_features)
        if n < 50:
            raise ValueError("Not enough samples for training")
        split = n - max(10, int(0.2 * n)) if val_size == 0 else n - val_size
        X_tr, y_tr = df_features.iloc[:split], target.iloc[:split]
        X_te = df_features.iloc[split:]
        self.fit(X_tr, y_tr)
        proba = self.predict_proba(X_te)
        sig = self.signals_from_proba(proba)
        out = pd.Series(sig, index=X_te.index, name="signal")
        return out
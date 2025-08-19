from __future__ import annotations
import numpy as np
from typing import Any
from sklearn.ensemble import RandomForestClassifier
from .registry import register_model

@register_model("random_forest")
class RFModel:
    def __init__(self, **params: Any):
        default = dict(
            n_estimators=300,
            max_depth=6,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1,
        )
        default.update(params or {})
        self.model = RandomForestClassifier(**default)
        self._is_fit = False

    def fit(self, X, y, eval_set=None, early_stopping_rounds=None):
        # RF has no native early stopping; we ignore.
        self.model.fit(X, y)
        self._is_fit = True

    def predict_proba(self, X) -> np.ndarray:
        if not self._is_fit:
            raise RuntimeError("Model not fitted")
        return self.model.predict_proba(X)
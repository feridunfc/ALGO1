from __future__ import annotations
import numpy as np
from typing import Optional, Dict, Any
from .registry import register_model

try:
    from xgboost import XGBClassifier  # type: ignore
    _XGB_AVAILABLE = True
except Exception:
    _XGB_AVAILABLE = False
    XGBClassifier = object  # stub

@register_model("xgboost")
class XGBModel:
    def __init__(self, **params: Any):
        if not _XGB_AVAILABLE:
            raise ImportError("xgboost is not installed; cannot instantiate 'xgboost' model")
        default = dict(
            n_estimators=500,
            max_depth=7,
            learning_rate=0.01,
            subsample=0.9,
            colsample_bytree=0.9,
            random_state=42,
            n_jobs=-1,
        )
        default.update(params or {})
        self.model = XGBClassifier(**default)
        self._is_fit = False

    def fit(self, X, y, eval_set=None, early_stopping_rounds: Optional[int] = 50):
        if eval_set is not None and early_stopping_rounds:
            self.model.fit(X, y, eval_set=eval_set, early_stopping_rounds=early_stopping_rounds, verbose=False)
        else:
            self.model.fit(X, y, verbose=False)
        self._is_fit = True

    def predict_proba(self, X) -> np.ndarray:
        if not self._is_fit:
            raise RuntimeError("Model not fitted")
        return self.model.predict_proba(X)
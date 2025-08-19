from __future__ import annotations
from typing import Any
import numpy as np
import pandas as pd

class BaseAIModel:
    def __init__(self, name: str, config: dict):
        self.name = name
        self.config = config
        self.model = None
        self._initialize_model({})
    def _initialize_model(self, params: dict | None = None):
        raise NotImplementedError
    def train(self, X: pd.DataFrame, y: pd.Series, **kwargs: Any) -> None:
        self.model.fit(X.values, y.values)
    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        if hasattr(self.model, "predict_proba"):
            p = self.model.predict_proba(X.values)
            if p.ndim == 2 and p.shape[1] >= 2:
                return p[:, 1]
            return p.ravel()
        else:
            pred = self.model.predict(X.values)
            return (pred > 0).astype(float)

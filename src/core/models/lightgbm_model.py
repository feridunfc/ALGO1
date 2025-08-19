from __future__ import annotations
import numpy as np, pandas as pd
from .base import BaseModel
try:
    import lightgbm as lgb; HAS_LGB=True
except Exception:
    HAS_LGB=False

class LightGBMModel(BaseModel):
    name="lightgbm"
    def __init__(self):
        if not HAS_LGB: raise ImportError("lightgbm not installed")
        self.model = lgb.LGBMClassifier(objective="binary", n_estimators=200, learning_rate=0.05)
    def fit(self, X: pd.DataFrame, y: pd.Series) -> None: self.model.fit(X, y)
    def predict_proba(self, X: pd.DataFrame) -> np.ndarray: return self.model.predict_proba(X)

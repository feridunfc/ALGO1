from __future__ import annotations
import numpy as np, pandas as pd
from .base import BaseModel
try:
    import xgboost as xgb; HAS_XGB=True
except Exception:
    HAS_XGB=False

class XGBoostModel(BaseModel):
    name="xgboost"
    def __init__(self):
        if not HAS_XGB: raise ImportError("xgboost not installed")
        self.model = xgb.XGBClassifier(n_estimators=300, max_depth=5, learning_rate=0.05, subsample=0.8, colsample_bytree=0.8, tree_method="hist", n_jobs=-1, eval_metric="logloss")
    def fit(self, X: pd.DataFrame, y: pd.Series) -> None: self.model.fit(X, y)
    def predict_proba(self, X: pd.DataFrame) -> np.ndarray: return self.model.predict_proba(X)

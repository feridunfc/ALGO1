from __future__ import annotations
import numpy as np
try:
    from xgboost import XGBClassifier
except Exception as e:
    raise

class XGBoostModel:
    def __init__(self, **kw):
        self.model = XGBClassifier(
            n_estimators=300,
            max_depth=5,
            subsample=0.8,
            colsample_bytree=0.8,
            learning_rate=0.05,
            random_state=42,
            n_jobs=-1,
            eval_metric="logloss"
        )

    def fit(self, X, y):
        self.model.fit(X, y)

    def predict_proba(self, X):
        p = self.model.predict_proba(X)
        if p.shape[1] == 1:
            return np.zeros(len(X), dtype=float)
        return p[:, 1]
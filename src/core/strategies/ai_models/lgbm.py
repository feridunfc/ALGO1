from __future__ import annotations
import numpy as np
try:
    import lightgbm as lgb
except Exception as e:
    raise

class LightGBMModel:
    def __init__(self, **kw):
        self.model = lgb.LGBMClassifier(
            n_estimators=400,
            max_depth=-1,
            subsample=0.8,
            colsample_bytree=0.8,
            learning_rate=0.05,
            random_state=42
        )

    def fit(self, X, y):
        self.model.fit(X, y)

    def predict_proba(self, X):
        p = self.model.predict_proba(X)
        if p.shape[1] == 1:
            return np.zeros(len(X), dtype=float)
        return p[:, 1]
from __future__ import annotations
import numpy as np
from sklearn.ensemble import RandomForestClassifier

class RandomForestModel:
    def __init__(self, **kw):
        self.model = RandomForestClassifier(
            n_estimators=200,
            max_depth=None,
            random_state=42,
            n_jobs=-1
        )

    def fit(self, X, y):
        self.model.fit(X, y)

    def predict_proba(self, X):
        # return prob of class 1
        p = self.model.predict_proba(X)
        if p.shape[1] == 1:
            # degenerate case
            return np.zeros(len(X), dtype=float)
        return p[:, 1]

from typing import Any
import numpy as np

class BaseModelAdapter:
    def fit(self, X, y): ...
    def predict_proba(self, X): ...
    def predict(self, X): ...

class SklearnRF(BaseModelAdapter):
    def __init__(self):
        from sklearn.ensemble import RandomForestClassifier
        self.m = RandomForestClassifier(n_estimators=200, random_state=42)
    def fit(self, X, y): self.m.fit(X,y)
    def predict_proba(self, X): return self.m.predict_proba(X)[:,1]
    def predict(self, X): return self.m.predict(X)

class SklearnLogReg(BaseModelAdapter):
    def __init__(self):
        from sklearn.linear_model import LogisticRegression
        self.m = LogisticRegression(max_iter=1000)
    def fit(self, X, y): self.m.fit(X,y)
    def predict_proba(self, X):
        try:
            return self.m.predict_proba(X)[:,1]
        except Exception:
            p = self.m.decision_function(X)
            return 1/(1+np.exp(-p))
    def predict(self, X): return self.m.predict(X)

def build_model(name: str) -> BaseModelAdapter | Any:
    name = name.lower()
    if name == "random_forest":
        return SklearnRF()
    if name == "logreg":
        return SklearnLogReg()
    raise ValueError(f"Unknown model: {name}")

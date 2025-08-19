from __future__ import annotations
import numpy as np, pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from .base import BaseModel

class RandomForestModel(BaseModel):
    name = "random_forest"
    def __init__(self, n_estimators: int = 200, max_depth: int = 5, random_state: int = 42):
        self.clf = RandomForestClassifier(n_estimators=n_estimators, max_depth=max_depth, n_jobs=-1, random_state=random_state)
    def fit(self, X: pd.DataFrame, y: pd.Series) -> None: self.clf.fit(X, y)
    def predict_proba(self, X: pd.DataFrame) -> np.ndarray: return self.clf.predict_proba(X)

class LogisticModel(BaseModel):
    name = "logistic_regression"
    def __init__(self): self.clf = LogisticRegression(max_iter=1000)
    def fit(self, X: pd.DataFrame, y: pd.Series) -> None: self.clf.fit(X, y)
    def predict_proba(self, X: pd.DataFrame) -> np.ndarray: return self.clf.predict_proba(X)

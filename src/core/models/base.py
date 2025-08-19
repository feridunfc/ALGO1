from __future__ import annotations
import pandas as pd, numpy as np

class BaseModel:
    name: str = "base"
    def fit(self, X: pd.DataFrame, y: pd.Series) -> None: raise NotImplementedError
    def predict_proba(self, X: pd.DataFrame) -> np.ndarray: raise NotImplementedError

def safe_predict_threshold(proba: np.ndarray, thr: float):
    if proba.ndim == 2 and proba.shape[1] == 2: p1 = proba[:,1]
    else: p1 = proba.reshape(-1)
    return (p1 >= thr).astype(float)

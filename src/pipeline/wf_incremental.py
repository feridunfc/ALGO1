from __future__ import annotations
import numpy as np
import pandas as pd
from typing import Callable, Dict
from sklearn.linear_model import SGDClassifier
from sklearn.model_selection import TimeSeriesSplit

class IncrementalWalkForward:
    """
    Online/partial_fit destekli WF runner.
    strategy_factory: () -> model  (SGDClassifier benzeri)
    """
    def __init__(self, strategy_factory: Callable[[], SGDClassifier], n_splits: int = 5, test_size: int = 63):
        self.factory = strategy_factory
        self.n_splits = n_splits
        self.test_size = test_size

    def run(self, X: pd.DataFrame, y: pd.Series) -> Dict[str, float]:
        tscv = TimeSeriesSplit(n_splits=self.n_splits, test_size=self.test_size)
        scores = []
        model = None
        classes = np.unique(y)
        for tr, te in tscv.split(X):
            Xtr, Xte = X.iloc[tr], X.iloc[te]
            ytr, yte = y.iloc[tr], y.iloc[te]
            if model is None:
                model = self.factory()
            for _ in range(3):  # mini-epoch
                model.partial_fit(Xtr, ytr, classes=classes)
            scores.append(float(model.score(Xte, yte)))
        return {"wf_accuracy": float(np.mean(scores))}

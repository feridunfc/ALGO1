
from __future__ import annotations
import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from sklearn.linear_model import SGDClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline

@dataclass
class OnlineLearner:
    classes_: tuple = (0, 1)
    loss: str = "log_loss"
    alpha: float = 1e-4
    random_state: int = 42
    _model: object = field(init=False, repr=False)

    def __post_init__(self):
        # StandardScaler + SGD partial_fit compatible pipeline
        self._model = make_pipeline(
            StandardScaler(with_mean=False),
            SGDClassifier(loss=self.loss, alpha=self.alpha, random_state=self.random_state, warm_start=True)
        )

    def partial_fit(self, X: pd.DataFrame, y: pd.Series):
        Xv = X.values if isinstance(X, pd.DataFrame) else X
        yv = y.values if isinstance(y, pd.Series) else y
        # partial_fit only on final estimator
        last_est = self._model.steps[-1][1]
        if not hasattr(last_est, "classes_"):
            last_est.partial_fit(Xv, yv, classes=np.array(self.classes_))
        else:
            last_est.partial_fit(Xv, yv)
        return self

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        # Pipeline predict_proba via decision_function if not available
        try:
            return self._model.predict_proba(X)
        except Exception:
            from sklearn.utils.extmath import softmax
            last_est = self._model.steps[-1][1]
            z = last_est.decision_function(X.values)
            if z.ndim == 1:
                z = np.vstack([-z, z]).T
            return softmax(z)

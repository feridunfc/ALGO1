from __future__ import annotations
import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import Any, Tuple
from sklearn.linear_model import SGDClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.utils.extmath import softmax


@dataclass
class OnlineLearner:
    classes_: Tuple[int, int] = (0, 1)
    loss: str = "log_loss"
    alpha: float = 1e-4
    random_state: int = 42

    _model: object = field(init=False, repr=False)
    _initialized: bool = field(default=False, init=False, repr=False)
    _scaler_fitted: bool = field(default=False, init=False, repr=False)

    def __post_init__(self):
        # Not: Pipeline'ın partial_fit'i yalnızca son adıma delege eder.
        # Bu yüzden scaler'ı biz ayrıca (partial_)fit + transform edeceğiz.
        self._model = make_pipeline(
            StandardScaler(with_mean=False),
            SGDClassifier(
                loss=self.loss,
                alpha=self.alpha,
                random_state=self.random_state,
                warm_start=True,
            ),
        )

    # ---- yardımcılar ----
    def _get_scaler(self) -> StandardScaler:
        return self._model.steps[0][1]

    def _get_estimator(self) -> SGDClassifier:
        return self._model.steps[-1][1]

    def _sanitize_xy(self, X, y):
        # X -> float64, NaN/±Inf -> 0.0
        if isinstance(X, (pd.DataFrame, pd.Series)):
            Xv = X.to_numpy()
        else:
            Xv = np.asarray(X)
        Xv = Xv.astype(np.float64, copy=False)
        Xv = np.nan_to_num(Xv, nan=0.0, posinf=0.0, neginf=0.0)

        # y -> int, NaN/±Inf -> 0
        if isinstance(y, (pd.Series, pd.DataFrame)):
            yv = y.to_numpy()
        else:
            yv = np.asarray(y)
        if yv.ndim > 1:
            yv = yv.ravel()
        yv = np.nan_to_num(yv, nan=0.0, posinf=0.0, neginf=0.0).astype(int, copy=False)
        return Xv, yv

    # ---- API ----
    def digest(self, payload: Any) -> str:
        import hashlib, pickle
        if isinstance(payload, pd.DataFrame):
            b = payload.to_csv(index=False).encode("utf-8")
            return hashlib.sha256(b).hexdigest()
        return hashlib.sha256(pickle.dumps(payload)).hexdigest()

    def partial_fit(self, X: pd.DataFrame, y: pd.Series):
        Xv, yv = self._sanitize_xy(X, y)

        # scaler'ı kademeli güncelle
        scaler = self._get_scaler()
        if hasattr(scaler, "partial_fit"):
            scaler.partial_fit(Xv)
            self._scaler_fitted = True
        else:
            if not self._scaler_fitted:
                scaler.fit(Xv)
                self._scaler_fitted = True

        X_t = scaler.transform(Xv)

        # son tahminciyi güncelle
        est = self._get_estimator()
        if not self._initialized or not hasattr(est, "classes_"):
            est.partial_fit(X_t, yv, classes=np.array(self.classes_))
            self._initialized = True
        else:
            est.partial_fit(X_t, yv)
        return self

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        # aynı sanitizasyon + transform
        if isinstance(X, (pd.DataFrame, pd.Series)):
            Xv = X.to_numpy(dtype=np.float64, copy=False)
        else:
            Xv = np.asarray(X, dtype=np.float64)
        Xv = np.nan_to_num(Xv, nan=0.0, posinf=0.0, neginf=0.0)

        scaler = self._get_scaler()
        if not self._scaler_fitted:
            # eğitimden önce predict çağrılırsa emniyet: ölçekleme yapmadan tahmin
            X_t = Xv
        else:
            X_t = scaler.transform(Xv)

        est = self._get_estimator()
        if hasattr(est, "predict_proba"):
            return est.predict_proba(X_t)

        # yedek: decision_function -> softmax
        z = est.decision_function(X_t)
        if z.ndim == 1:  # binary
            z = np.vstack([-z, z]).T
        return softmax(z)

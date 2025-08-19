from __future__ import annotations
import numpy as np, pandas as pd
from ...models.registry import list_models, get_model
from ...models.base import safe_predict_threshold
from ....features.ta_features import make_basic_features

class AIUnified:
    name = "ai_unified"
    def __init__(self, models=None, train_ratio: float = 0.7, threshold: float = 0.5):
        self.models = models or ["random_forest"]
        self.train_ratio = float(train_ratio)
        self.threshold = float(threshold)

    def _build_xy(self, df: pd.DataFrame):
        X, y = make_basic_features(df)
        mask = X.notna().all(axis=1) & y.notna()
        return X.loc[mask], y.loc[mask]

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        X, y = self._build_xy(df)
        n_train = max(30, int(len(X) * self.train_ratio))
        Xtr, ytr = X.iloc[:n_train], y.iloc[:n_train]
        Xte = X.iloc[n_train:]
        probs = []
        for mname in self.models:
            try:
                m = get_model(mname)
                m.fit(Xtr, ytr)
                proba = m.predict_proba(Xte)
                if proba.ndim == 2 and proba.shape[1] == 2: probs.append(proba[:,1])
                else: probs.append(proba.reshape(-1))
            except Exception:
                continue
        if not probs:
            return pd.Series(0.0, index=df.index, name="signal")
        p = np.mean(probs, axis=0)
        raw_sig = safe_predict_threshold(p, self.threshold).astype(float)
        sig = pd.Series(0.0, index=X.index)
        sig.loc[Xte.index] = raw_sig
        return sig.reindex(df.index).fillna(0.0).rename("signal")

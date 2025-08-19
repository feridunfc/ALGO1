from __future__ import annotations
import numpy as np
import pandas as pd
from typing import Optional, Dict, Any

# Optional heavy deps
def _try_import_xgb():
    try:
        import xgboost as xgb  # noqa
        return xgb
    except Exception:
        return None

def _try_import_lgbm():
    try:
        import lightgbm as lgb  # noqa
        return lgb
    except Exception:
        return None

def _try_import_cat():
    try:
        import catboost as cat  # noqa
        return cat
    except Exception:
        return None

from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression

MODEL_REGISTRY = {}

def register_model(name):
    def _wrap(cls):
        MODEL_REGISTRY[name] = cls
        return cls
    return _wrap

@register_model("random_forest")
class RFModel:
    def __init__(self, **kwargs):
        self.model = RandomForestClassifier(
            n_estimators=kwargs.get("n_estimators", 200),
            max_depth=kwargs.get("max_depth", 5),
            random_state=42,
            n_jobs=-1
        )

    def fit(self, X, y):
        self.model.fit(X, y)

    def predict_proba(self, X):
        proba = self.model.predict_proba(X)[:, 1]
        return proba

@register_model("logistic_regression")
class LogRegModel:
    def __init__(self, **kwargs):
        self.model = LogisticRegression(max_iter=1000, n_jobs=None)

    def fit(self, X, y):
        self.model.fit(X, y)

    def predict_proba(self, X):
        proba = self.model.predict_proba(X)[:, 1]
        return proba

# Optional models
xgb = _try_import_xgb()
if xgb is not None:
    @register_model("xgboost")
    class XGBModel:
        def __init__(self, **kwargs):
            self.model = xgb.XGBClassifier(
                n_estimators=kwargs.get("n_estimators", 200),
                max_depth=kwargs.get("max_depth", 4),
                learning_rate=kwargs.get("learning_rate", 0.05),
                subsample=kwargs.get("subsample", 0.8),
                colsample_bytree=kwargs.get("colsample_bytree", 0.8),
                random_state=42,
                n_jobs=-1
            )
        def fit(self, X, y):
            self.model.fit(X, y)
        def predict_proba(self, X):
            return self.model.predict_proba(X)[:, 1]

lgb = _try_import_lgbm()
if lgb is not None:
    @register_model("lightgbm")
    class LGBModel:
        def __init__(self, **kwargs):
            self.model = lgb.LGBMClassifier(
                n_estimators=kwargs.get("n_estimators", 400),
                max_depth=kwargs.get("max_depth", -1),
                learning_rate=kwargs.get("learning_rate", 0.05),
                subsample=kwargs.get("subsample", 0.8),
                colsample_bytree=kwargs.get("colsample_bytree", 0.8),
                random_state=42,
                n_jobs=-1
            )
        def fit(self, X, y):
            self.model.fit(X, y)
        def predict_proba(self, X):
            return self.model.predict_proba(X)[:, 1]

cat = _try_import_cat()
if cat is not None:
    @register_model("catboost")
    class CATModel:
        def __init__(self, **kwargs):
            self.model = cat.CatBoostClassifier(
                iterations=kwargs.get("iterations", 300),
                depth=kwargs.get("depth", 6),
                learning_rate=kwargs.get("learning_rate", 0.05),
                verbose=False,
                random_state=42
            )
        def fit(self, X, y):
            self.model.fit(X, y)
        def predict_proba(self, X):
            return self.model.predict_proba(X)[:, 1]

def list_models():
    return sorted(MODEL_REGISTRY.keys())

class AIUnifiedStrategy:
    def __init__(self, model_type: str = "random_forest", train_ratio: float = 0.7,
                 threshold: float = 0.5, **kwargs):
        assert model_type in MODEL_REGISTRY, f"Unknown model_type {model_type}"
        self.model = MODEL_REGISTRY[model_type](**kwargs)
        self.train_ratio = float(train_ratio)
        self.threshold = float(threshold)

    def _make_xy(self, df: pd.DataFrame):
        # Features (no look-ahead): use lagged returns, rsi, sma distances
        X = pd.DataFrame({
            'ret1_lag1': df['close'].pct_change().shift(1).fillna(0.0),
            'rsi_14': df.get('rsi_14', pd.Series(index=df.index, dtype=float)).fillna(50.0),
            'sma_10_dist': (df['close'] / df['sma_10'] - 1.0).fillna(0.0),
            'sma_50_dist': (df['close'] / df['sma_50'] - 1.0).fillna(0.0),
            'vol_20': df.get('vol_20', pd.Series(index=df.index, dtype=float)).fillna(0.0),
        })
        y = (df['close'].pct_change().shift(-1) > 0).astype(int)  # predict next-bar up (shifted future)
        X, y = X.iloc[50:].copy(), y.iloc[50:].copy()  # drop warm-up
        return X, y

    def generate_signal(self, df: pd.DataFrame) -> pd.Series:
        X, y = self._make_xy(df)
        n = len(X)
        split = max(int(n * self.train_ratio), 1)
        X_tr, y_tr = X.iloc[:split], y.iloc[:split]
        X_te = X.iloc[split:]
        self.model.fit(X_tr, y_tr)
        proba = pd.Series(self.model.predict_proba(X_te), index=X_te.index, name='proba')
        sig = (proba > self.threshold).astype(int) * 2 - 1  # 1->BUY, 0->SELL
        # Align to original df index, shift to avoid look-ahead
        out = pd.Series(0.0, index=df.index, name='signal')
        out.loc[sig.index] = sig.astype(float)
        # delay will be applied by backtest; still we ensure execution-friendly shape
        return out.fillna(0.0)

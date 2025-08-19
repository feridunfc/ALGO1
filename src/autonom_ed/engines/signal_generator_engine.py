import numpy as np
from .feature_engineer_engine import FeatureEngineerEngine

class BaseStrategy:
    def signal_for_bar(self, features: dict) -> int:
        raise NotImplementedError

class SMACrossoverStrategy(BaseStrategy):
    def __init__(self, ma_fast=20, ma_slow=50):
        self.ma_fast = ma_fast
        self.ma_slow = ma_slow

    def signal_for_bar(self, features: dict) -> int:
        sf = features.get("sma_fast", np.nan)
        sl = features.get("sma_slow", np.nan)
        if np.isnan(sf) or np.isnan(sl):
            return 0
        return 1 if sf > sl else -1 if sf < sl else 0

# --- AI Model Adapter (sklearn-like) ---
class SklearnLikeAdapter(BaseStrategy):
    def __init__(self, model, feature_keys, threshold=0.5):
        self.model = model
        self.feature_keys = feature_keys
        self.threshold = threshold

    def signal_for_bar(self, features: dict) -> int:
        import numpy as np
        X = np.array([[features.get(k, np.nan) for k in self.feature_keys]], dtype=float)
        # Simple impute nans with 0
        X = np.nan_to_num(X, nan=0.0)
        # Try predict_proba else decision_function/predict
        proba = None
        if hasattr(self.model, "predict_proba"):
            proba = float(self.model.predict_proba(X)[0,1])
        elif hasattr(self.model, "decision_function"):
            score = float(self.model.decision_function(X)[0])
            proba = 1.0/(1.0+np.exp(-score))
        else:
            pred = int(self.model.predict(X)[0])
            return 1 if pred > 0 else -1 if pred < 0 else 0
        # Long if proba>thr, short if < (1-thr)
        if proba > self.threshold:
            return 1
        elif proba < 1.0 - self.threshold:
            return -1
        return 0

# --- Registry ---
def build_strategy(name: str, params: dict):
    name = name.lower()
    if name in ("sma", "sma_crossover"):
        return SMACrossoverStrategy(ma_fast=params.get("ma_fast",20), ma_slow=params.get("ma_slow",50))
    elif name in ("rf","logreg","xgb","lgbm","catboost"):
        # Build a simple model (untrained dummy). In practice, you should fit it beforehand
        from ..models.registry import get_model
        model = get_model(name, params.get(name, {}))
        # default feature set
        fkeys = params.get("feature_keys", ["ret1","sma_fast","sma_slow"])
        thr = params.get("threshold", 0.55)
        return SklearnLikeAdapter(model, fkeys, threshold=thr)
    else:
        raise ValueError(f"Unknown strategy: {name}")

import pandas as pd, numpy as np
from ..base import Strategy
from ..features import make_basic_features, target_next_up

class XGBoostStrictStrategy(Strategy):
    name = "ai_xgboost"
    def __init__(self, **params):
        try:
            import xgboost as xgb
        except Exception:
            self._disabled = True
            self.model = None
            return
        self._disabled = False
        self.model = xgb.XGBClassifier(
            n_estimators=params.get("n_estimators", 200),
            max_depth=params.get("max_depth", 4),
            learning_rate=params.get("learning_rate", 0.05),
            subsample=params.get("subsample", 0.8),
            colsample_bytree=params.get("colsample_bytree", 0.8),
            n_jobs=1, eval_metric="logloss", tree_method="hist"
        )
    def fit(self, df):
        if getattr(self, "_disabled", False): return
        X = make_basic_features(df).iloc[:-1]; y = target_next_up(df).iloc[:-1]; self.model.fit(X,y)
    def predict_proba(self, df):
        X = make_basic_features(df)
        if getattr(self, "_disabled", False):
            return pd.Series(0.5, index=df.index)
        p = self.model.predict_proba(X)[:,1]
        return pd.Series(p, index=df.index).clip(0,1)

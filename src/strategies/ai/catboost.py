import pandas as pd, numpy as np
from ..base import Strategy
from ..features import make_basic_features, target_next_up

class CatBoostStrategy(Strategy):
    name = "ai_catboost"
    def __init__(self, **params):
        try:
            from catboost import CatBoostClassifier
            self._disabled = False
            self.model = CatBoostClassifier(
                iterations=params.get("iterations", 300),
                depth=params.get("depth", 6),
                learning_rate=params.get("learning_rate", 0.05),
                loss_function="Logloss",
                verbose=False
            )
        except Exception:
            self._disabled = True
            self.model = None
    def fit(self, df):
        if self._disabled: return
        X = make_basic_features(df).iloc[:-1]; y = target_next_up(df).iloc[:-1]; self.model.fit(X,y)
    def predict_proba(self, df):
        X = make_basic_features(df)
        if self._disabled: return pd.Series(0.5, index=df.index)
        p = self.model.predict_proba(X)[:,1]
        return pd.Series(p, index=df.index).clip(0,1)

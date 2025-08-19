import pandas as pd, numpy as np
from ..base import Strategy
from ..features import make_basic_features, target_next_up

class TreeBoostStrategy(Strategy):
    name = "ai_tree_boost"
    def __init__(self, **params):
        self.params = {"n_estimators": 200, "max_depth": 4, "learning_rate": 0.05}
        self.params.update(params)
        try:
            import xgboost as xgb
            self._lib = "xgb"
            self.model = xgb.XGBClassifier(
                n_estimators=self.params["n_estimators"],
                max_depth=self.params["max_depth"],
                learning_rate=self.params["learning_rate"],
                subsample=self.params.get("subsample", 0.8),
                colsample_bytree=self.params.get("colsample_bytree", 0.8),
                n_jobs=1,
                eval_metric="logloss",
                tree_method="hist"
            )
        except Exception:
            from sklearn.ensemble import GradientBoostingClassifier
            self._lib = "sk"
            self.model = GradientBoostingClassifier(
                n_estimators=self.params["n_estimators"],
                max_depth=self.params["max_depth"],
                learning_rate=self.params["learning_rate"]
            )

    def fit(self, df: pd.DataFrame) -> None:
        X = make_basic_features(df).iloc[:-1]
        y = target_next_up(df).iloc[:-1]
        self.model.fit(X, y)

    def predict_proba(self, df: pd.DataFrame) -> pd.Series:
        X = make_basic_features(df)
        try:
            p = self.model.predict_proba(X)[:,1]
        except Exception:
            try:
                p = (self.model.decision_function(X) - X.shape[1]) / (2*X.shape[1])
            except Exception:
                p = np.full(len(X), 0.5)
        return pd.Series(p, index=df.index).clip(0.0, 1.0)

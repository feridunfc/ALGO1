import pandas as pd, numpy as np
from ..base import Strategy
from ..features import make_basic_features, target_next_up
from sklearn.linear_model import LogisticRegression

class LogisticStrategy(Strategy):
    name = "ai_logistic"
    def __init__(self):
        self.model = LogisticRegression(max_iter=500)
    def fit(self, df):
        X = make_basic_features(df).iloc[:-1]; y = target_next_up(df).iloc[:-1]; self.model.fit(X, y)
    def predict_proba(self, df):
        X = make_basic_features(df); p = self.model.predict_proba(X)[:,1]
        return pd.Series(p, index=df.index).clip(0,1)

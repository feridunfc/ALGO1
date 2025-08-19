import pandas as pd, numpy as np
from ..base import Strategy
from ..features import make_basic_features, target_next_up
from sklearn.ensemble import RandomForestClassifier

class RandomForestStrategy(Strategy):
    name = "ai_random_forest"
    def __init__(self, n_estimators=200, max_depth=6):
        self.model = RandomForestClassifier(n_estimators=n_estimators, max_depth=max_depth, n_jobs=1, random_state=42)
    def fit(self, df): 
        X = make_basic_features(df).iloc[:-1]; y = target_next_up(df).iloc[:-1]; self.model.fit(X,y)
    def predict_proba(self, df):
        X = make_basic_features(df); p = self.model.predict_proba(X)[:,1]; 
        return pd.Series(p, index=df.index).clip(0,1)

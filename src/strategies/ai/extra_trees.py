import pandas as pd
from ..base import Strategy
from ..features import make_basic_features, target_next_up
from sklearn.ensemble import ExtraTreesClassifier

class ExtraTreesStrategy(Strategy):
    name = "ai_extra_trees"
    def __init__(self, n_estimators=300, max_depth=None):
        self.model = ExtraTreesClassifier(n_estimators=n_estimators, max_depth=max_depth, random_state=42, n_jobs=1)
    def fit(self, df): 
        X = make_basic_features(df).iloc[:-1]; y = target_next_up(df).iloc[:-1]; self.model.fit(X,y)
    def predict_proba(self, df):
        X = make_basic_features(df); p = self.model.predict_proba(X)[:,1]; 
        return pd.Series(p, index=df.index).clip(0,1)

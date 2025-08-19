import pandas as pd, numpy as np
from ..base import Strategy
from ..features import make_basic_features, target_next_up
from sklearn.svm import SVC

class SVMStrategy(Strategy):
    name = "ai_svm"
    def __init__(self, C=1.0, gamma="scale"):
        self.model = SVC(C=C, gamma=gamma, probability=True)
    def fit(self, df):
        X = make_basic_features(df).iloc[:-1]; y = target_next_up(df).iloc[:-1]; self.model.fit(X,y)
    def predict_proba(self, df):
        X = make_basic_features(df)
        try:
            p = self.model.predict_proba(X)[:,1]
        except Exception:
            d = self.model.decision_function(X)
            p = 1/(1+np.exp(-d))
        return pd.Series(p, index=df.index).clip(0,1)

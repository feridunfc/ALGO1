import pandas as pd
from ..base import Strategy
from ..features import make_basic_features, target_next_up
from sklearn.naive_bayes import GaussianNB

class NaiveBayesStrategy(Strategy):
    name = "ai_naive_bayes"
    def __init__(self):
        self.model = GaussianNB()
    def fit(self, df):
        X = make_basic_features(df).iloc[:-1]; y = target_next_up(df).iloc[:-1]; self.model.fit(X,y)
    def predict_proba(self, df):
        X = make_basic_features(df); p = self.model.predict_proba(X)[:,1]
        return pd.Series(p, index=df.index).clip(0,1)

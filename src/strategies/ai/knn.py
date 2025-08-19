import pandas as pd
from ..base import Strategy
from ..features import make_basic_features, target_next_up
from sklearn.neighbors import KNeighborsClassifier

class KNNStrategy(Strategy):
    name = "ai_knn"
    def __init__(self, n_neighbors=5):
        self.model = KNeighborsClassifier(n_neighbors=n_neighbors)
    def fit(self, df):
        X = make_basic_features(df).iloc[:-1]; y = target_next_up(df).iloc[:-1]; self.model.fit(X,y)
    def predict_proba(self, df):
        X = make_basic_features(df); p = self.model.predict_proba(X)[:,1]
        return pd.Series(p, index=df.index).clip(0,1)

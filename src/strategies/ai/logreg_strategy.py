from __future__ import annotations
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from ..base_strategy import BaseStrategy
from ..strategy_factory import register

@register("ai_logreg")
class LogisticRegressionStrategy(BaseStrategy):
    def __init__(self, name: str="ai_logreg", **kwargs):
        super().__init__(name)
        self.scaler = StandardScaler()
        self.model = LogisticRegression(max_iter=1000)

    def train(self, features_df: pd.DataFrame):
        X = features_df[["sma_fast","sma_slow","rsi","vol"]].values
        y = (features_df["ret"].shift(-1) > 0).astype(int)  # next-bar up/down
        y = y.iloc[:-1]
        X = X[:-1]
        Xs = self.scaler.fit_transform(X)
        self.model.fit(Xs, y)
        self.is_trained = True

    def predict(self, features_df: pd.DataFrame) -> pd.Series:
        if not self.is_trained:
            # train on the fly with available history
            if len(features_df) > 200:
                self.train(features_df)
            else:
                return pd.Series(0, index=features_df.index, name="signal")
        X = features_df[["sma_fast","sma_slow","rsi","vol"]].values
        Xs = self.scaler.transform(X)
        proba = self.model.predict_proba(Xs)[:,1]
        sig = (proba >= 0.5).astype(int)*2 - 1  # 1 for long, -1 for short
        return pd.Series(sig, index=features_df.index, name="signal")

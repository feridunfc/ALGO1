from __future__ import annotations
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from ..base_strategy import BaseStrategy
from ..strategy_factory import register

@register("ai_random_forest")
class RandomForestStrategy(BaseStrategy):
    def __init__(self, name: str="ai_random_forest", n_estimators: int = 200, **kwargs):
        super().__init__(name)
        self.scaler = StandardScaler()
        self.model = RandomForestClassifier(n_estimators=n_estimators, random_state=42)

    def train(self, features_df: pd.DataFrame):
        X = features_df[["sma_fast","sma_slow","rsi","vol"]].values
        y = (features_df["ret"].shift(-1) > 0).astype(int)
        y = y.iloc[:-1]
        X = X[:-1]
        Xs = self.scaler.fit_transform(X)
        self.model.fit(Xs, y)
        self.is_trained = True

    def predict(self, features_df: pd.DataFrame) -> pd.Series:
        if not self.is_trained:
            if len(features_df) > 200:
                self.train(features_df)
            else:
                return pd.Series(0, index=features_df.index, name="signal")
        X = features_df[["sma_fast","sma_slow","rsi","vol"]].values
        Xs = self.scaler.transform(X)
        proba = getattr(self.model, "predict_proba", None)
        if proba is not None:
            p = self.model.predict_proba(Xs)[:,1]
            sig = (p >= 0.5).astype(int)*2 - 1
        else:
            pred = self.model.predict(Xs)
            sig = pred*2 - 1
        return pd.Series(sig, index=features_df.index, name="signal")

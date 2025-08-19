import pandas as pd, numpy as np
from ..base import Strategy
from ..ai.random_forest import RandomForestStrategy
from ..ai.logistic import LogisticStrategy
from ..rule_based.macd_signal import MACDSignal

class WeightedEnsemble(Strategy):
    name = "hy_weighted_ensemble"
    def __init__(self, w=(0.4, 0.4, 0.2)):
        self.m1 = RandomForestStrategy(); self.m2 = LogisticStrategy(); self.m3 = MACDSignal()
        self.w = w
    def fit(self, df): 
        self.m1.fit(df); self.m2.fit(df)
    def predict_proba(self, df: pd.DataFrame) -> pd.Series:
        p1 = self.m1.predict_proba(df); p2 = self.m2.predict_proba(df); p3 = self.m3.predict_proba(df)
        out = self.w[0]*p1 + self.w[1]*p2 + self.w[2]*p3
        return out.clip(0,1)

import pandas as pd
from ..base import Strategy
from ..rule_based.ma_crossover import MACrossover
from ..ai.random_forest import RandomForestStrategy

class RegimeSwitcher(Strategy):
    name = "hy_regime_switcher"
    def __init__(self):
        self.trend_model = MACrossover()
        self.ai_model = RandomForestStrategy()
    def fit(self, df: pd.DataFrame) -> None:
        self.ai_model.fit(df)
    def predict_proba(self, df: pd.DataFrame) -> pd.Series:
        trend = self.trend_model.predict_proba(df)
        ai = self.ai_model.predict_proba(df)
        # If trend bullish (p>0.55) → blend towards AI, else neutralize
        out = 0.5 + (ai - 0.5) * (trend > 0.55).astype(float)
        return out.clip(0,1)

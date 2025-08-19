import pandas as pd
from ..base import Strategy
from ..rule_based.bollinger_reversion import BollingerReversion
from ..ai.tree_boost import TreeBoostStrategy

class RuleFilterAI(Strategy):
    name = "hy_rule_filter_ai"
    def __init__(self, rule=None, ai=None):
        self.rule = rule or BollingerReversion()
        self.ai = ai or TreeBoostStrategy()
    def fit(self, df): self.ai.fit(df)
    def predict_proba(self, df: pd.DataFrame) -> pd.Series:
        rp = self.rule.predict_proba(df); ap = self.ai.predict_proba(df)
        mask = (rp > 0.55) | (rp < 0.45)
        out = pd.Series(0.5, index=df.index)
        out[mask] = ap[mask]
        return out.clip(0,1)

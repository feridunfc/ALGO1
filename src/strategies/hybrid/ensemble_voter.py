import pandas as pd
from typing import List
from ..base import Strategy
from ..rule_based.ma_crossover import MACrossover
from ..rule_based.breakout import Breakout
from ..ai.tree_boost import TreeBoostStrategy

REGISTRY = {
    "rb_ma_crossover": MACrossover,
    "rb_breakout": Breakout,
    "ai_tree_boost": TreeBoostStrategy
}

class EnsembleVoter(Strategy):
    name = "hy_ensemble_voter"
    def __init__(self, members: List[str] = None, min_agreement: int = 2):
        if members is None:
            members = ["rb_ma_crossover", "rb_breakout", "ai_tree_boost"]
        self.members = [REGISTRY[m]() for m in members]
        self.min_agreement = min_agreement
    def predict_proba(self, df: pd.DataFrame) -> pd.Series:
        probas = [m.predict_proba(df) for m in self.members]
        votes = sum([(p>0.55).astype(int) - (p<0.45).astype(int) for p in probas])
        out = (votes*0).astype(float) + 0.5
        out[votes >= self.min_agreement] = 0.75
        out[votes <= -self.min_agreement] = 0.25
        return out.clip(0,1)

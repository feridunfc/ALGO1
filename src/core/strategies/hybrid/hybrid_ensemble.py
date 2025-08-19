from __future__ import annotations
import pandas as pd
from . . .conventional.ma_crossover import MovingAverageCrossover  # noqa: E402
from . . .ai.ai_unified import AIUnified  # noqa: E402

class HybridEnsemble:
    name = "hybrid_ensemble"
    def __init__(self, ma_fast: int = 20, ma_slow: int = 50, models=None, threshold: float = 0.5):
        self.rule = MovingAverageCrossover(ma_fast=ma_fast, ma_slow=ma_slow)
        self.ai = AIUnified(models=models or ["random_forest"], threshold=threshold)
    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        s_rule = self.rule.generate_signals(df)
        s_ai = self.ai.generate_signals(df)
        return ((s_rule + s_ai) / 2.0).clip(-1.0, 1.0).rename("signal")

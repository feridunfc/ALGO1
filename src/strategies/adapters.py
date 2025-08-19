# src/strategies/adapters.py
import pandas as pd
from .base import Strategy

class WalkForwardAdapter(Strategy):
    def __init__(self, base_strategy: Strategy):
        self.base = base_strategy
        self.is_wf_compatible = True

    def retrain(self, df: pd.DataFrame):
        if hasattr(self.base, "retrain"):
            self.base.retrain(df)
        elif hasattr(self.base, "fit"):
            self.base.fit(df)

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        if hasattr(self.base, "generate_signals"):
            return self.base.generate_signals(data)
        if hasattr(self.base, "predict_proba"):
            proba = self.base.predict_proba(data)
            return self.base.to_signals(proba)
        return pd.Series(0, index=data.index)

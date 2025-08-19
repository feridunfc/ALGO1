import pandas as pd
from ..base import Strategy

class LSTMStrategy(Strategy):
    name = "ai_lstm"
    def __init__(self, hidden=32, layers=1, lookback=60):
        self.hidden=hidden; self.layers=layers; self.lookback=lookback
        try:
            import torch  # noqa
            self._available = True
        except Exception:
            self._available = False
    def fit(self, df): pass
    def predict_proba(self, df: pd.DataFrame) -> pd.Series:
        # Neutral if heavy deps not present
        return pd.Series(0.5, index=df.index)

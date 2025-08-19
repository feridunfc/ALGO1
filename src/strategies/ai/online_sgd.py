
import pandas as pd
import numpy as np
from dataclasses import dataclass
from src.ai.online_learner import OnlineLearner
from src.strategies.plugins.auto_register import try_register

@dataclass
class OnlineSGDStrategy:
    name: str = "ai_online_sgd"
    threshold: float = 0.55

    def fit(self, data: pd.DataFrame):
        self.ol = OnlineLearner()
        X = pd.DataFrame({
            "ret1": data["close"].pct_change().shift(1).fillna(0.0),
            "ret5": data["close"].pct_change(5).shift(1).fillna(0.0),
            "vol20": data["close"].pct_change().rolling(20, min_periods=10).std().shift(1).fillna(0.0)
        }, index=data.index)
        y = (data["close"].pct_change().shift(-1) > 0).astype(int).fillna(0)
        self.ol.partial_fit(X.iloc[20:], y.iloc[20:])
        return self

    def predict_proba(self, data: pd.DataFrame) -> pd.Series:
        X = pd.DataFrame({
            "ret1": data["close"].pct_change().shift(1).fillna(0.0),
            "ret5": data["close"].pct_change(5).shift(1).fillna(0.0),
            "vol20": data["close"].pct_change().rolling(20, min_periods=10).std().shift(1).fillna(0.0)
        }, index=data.index)
        import numpy as np
        p = self.ol.predict_proba(X)[:, 1]
        return pd.Series(np.clip(p, 0, 1), index=data.index)

# auto-register
try_register("ai_online_sgd", OnlineSGDStrategy)

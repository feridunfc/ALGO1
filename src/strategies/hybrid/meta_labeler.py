import pandas as pd, numpy as np
from ..base import Strategy
from ..ai.tree_boost import TreeBoostStrategy
from .ensemble_voter import EnsembleVoter

def _regime_features(df: pd.DataFrame) -> pd.DataFrame:
    r1 = df["close"].pct_change()
    vol20 = r1.rolling(20, min_periods=20).std(ddof=0)
    ma10 = df["close"].rolling(10, min_periods=10).mean()
    ma20 = df["close"].rolling(20, min_periods=20).mean()
    trend = (ma10 > ma20).astype(float)
    return pd.DataFrame({"trend": trend.fillna(0), "vol20": vol20.fillna(0)})

def _sentiment_feature(df: pd.DataFrame) -> pd.Series:
    for col in ("sentiment","news_sentiment"):
        if col in df.columns: return df[col].fillna(0.0)
    return pd.Series(0.0, index=df.index)

class MetaLabeler(Strategy):
    name = "hy_meta_labeler"
    def __init__(self, base=None, meta=None):
        self.base = base or EnsembleVoter()
        self.meta = meta or TreeBoostStrategy()
    def fit(self, df: pd.DataFrame) -> None:
        base_p = self.base.predict_proba(df)
        reg = _regime_features(df); sent = _sentiment_feature(df)
        X = pd.concat([pd.DataFrame({"base_proba": base_p}), reg, sent.rename("sent")], axis=1)
        y = (df["close"].pct_change().shift(-1) > 0).astype(int)
        self.meta.model.fit(X.iloc[:-1], y.iloc[:-1])
    def predict_proba(self, df: pd.DataFrame) -> pd.Series:
        base_p = self.base.predict_proba(df)
        reg = _regime_features(df); sent = _sentiment_feature(df)
        X = pd.concat([pd.DataFrame({"base_proba": base_p}), reg, sent.rename("sent")], axis=1)
        try:
            p = self.meta.model.predict_proba(X)[:,1]
        except Exception:
            p = base_p.values
        return pd.Series(p, index=df.index).clip(0,1)

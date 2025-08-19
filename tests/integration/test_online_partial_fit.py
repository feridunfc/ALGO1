
import pandas as pd, numpy as np
from src.ai.online_learner import OnlineLearner

def test_partial_fit_runs():
    idx = pd.date_range('2023-01-01', periods=200, freq='D')
    close = 100 + np.cumsum(np.random.normal(0,1,len(idx)))
    X = pd.DataFrame({'x1': pd.Series(close).pct_change().fillna(0.0)}, index=idx)
    y = (pd.Series(close).pct_change().shift(-1) > 0).astype(int).fillna(0)
    ol = OnlineLearner()
    ol.partial_fit(X.iloc[10:], y.iloc[10:])
    p = ol.predict_proba(X.iloc[50:60])
    assert p.shape[0] == 10

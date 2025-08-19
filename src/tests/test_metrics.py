import pandas as pd
from datetime import datetime, timedelta
from autonom_ed.engines.metrics_engine import summarize

def test_metrics_basic():
    idx = pd.date_range("2020-01-01", periods=10, freq="D")
    eq = pd.Series(100000.0*(1.01)**(range(10)), index=idx)
    m = summarize(eq)
    assert "CAGR" in m and "Sharpe" in m

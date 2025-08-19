import importlib
import pandas as pd
import pytest

def test_backtest_engine_smoke():
    try:
        engine_mod = importlib.import_module("src.backtest.engine")
    except Exception:
        pytest.skip("Backtest engine module not found; skipping smoke.")
    BacktestEngine = getattr(engine_mod, "BacktestEngine", None)
    if BacktestEngine is None:
        pytest.skip("BacktestEngine not found; skipping smoke.")

    # sample strategy (no-op)
    class DummyStrat:
        def fit(self, df): pass
        def predict_proba(self, df): return pd.Series(0.5, index=df.index)

    # sample data
    df = pd.read_csv("tests/fixtures/golden_sample.csv", parse_dates=["timestamp"], index_col="timestamp")
    eng = BacktestEngine()
    res = eng.run(data=df, strategy=DummyStrat())
    assert hasattr(res, "equity_curve")

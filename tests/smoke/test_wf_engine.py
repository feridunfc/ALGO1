# tests/smoke/test_wf_engine.py
import pandas as pd
from src.backtest.wf_engine import WalkForwardEngine, BacktestEngine
from src.strategies.xgboost_strategy import XGBoostStrategy

def test_wf_engine_runs():
    df = pd.read_csv("tests/golden/input_golden.csv", parse_dates=["timestamp"], index_col="timestamp")
    rep = WalkForwardEngine(BacktestEngine).run(XGBoostStrategy(), df)
    frame = rep.to_frame()
    assert not frame.empty
    agg = rep.aggregate()
    assert "sharperatio" in frame.columns or "sharperatio" in {k.lower() for k in agg.keys()}

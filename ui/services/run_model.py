import pandas as pd
from pathlib import Path
from ...src.strategies.registry import STRATEGY_REGISTRY
from ...src.backtest.risk_execution_adapter import RiskExecutionAdapter

def _load_fixture():
    df = pd.read_csv("tests/fixtures/golden_sample.csv", parse_dates=["timestamp"], index_col="timestamp")
    return {"AAA": df, "BBB": df.copy()}

def run(strategy_key: str):
    data = _load_fixture()
    strat = STRATEGY_REGISTRY[strategy_key]()
    eng = RiskExecutionAdapter(primary_symbol="AAA", sector_map={"AAA":"technology","BBB":"technology"})
    return eng.run(data, strat)

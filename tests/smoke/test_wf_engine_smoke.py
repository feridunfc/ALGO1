import pandas as pd
from src.backtest.wf_engine import WalkForwardEngine
from src.strategies.registry import STRATEGY_REGISTRY

def test_wf_runs_and_aggregates():
    df = pd.read_csv("tests/fixtures/golden_sample.csv", parse_dates=["timestamp"], index_col="timestamp")
    strat = STRATEGY_REGISTRY["rb_ma_crossover"]()
    wf = WalkForwardEngine(n_splits=3, test_size=30)
    rep = wf.run(strat, df)
    agg = rep.aggregate()
    assert set(agg.keys()) == {"sharpe","max_dd","win_rate","turnover"}

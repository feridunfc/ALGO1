import pandas as pd, json
from pathlib import Path
from ...src.strategies.registry import STRATEGY_REGISTRY
from ...src.backtest.wf_engine import WalkForwardEngine
from ...optimization.hpo_engine import HPOEngine

def _load_fixture():
    path1 = Path("tests/fixtures/golden_sample.csv")
    if path1.exists():
        return pd.read_csv(path1, parse_dates=["timestamp"], index_col="timestamp")
    raise FileNotFoundError("tests/fixtures/golden_sample.csv missing")

def run_wf_for_strategy(strategy_key: str, data: pd.DataFrame = None, wf_splits: int = 5, wf_test: int = 63):
    data = data if data is not None else _load_fixture()
    Strat = STRATEGY_REGISTRY[strategy_key]
    strat = Strat()
    wf = WalkForwardEngine(n_splits=wf_splits, test_size=wf_test)
    report = wf.run(strat, data)
    agg = report.aggregate()
    agg["strategy"] = strategy_key
    return agg

def run_wf_batch(strategy_keys, data: pd.DataFrame = None, wf_splits: int = 5, wf_test: int = 63) -> pd.DataFrame:
    rows = []
    for key in strategy_keys:
        rows.append(run_wf_for_strategy(key, data=data, wf_splits=wf_splits, wf_test=wf_test))
    df = pd.DataFrame(rows).set_index("strategy")
    # order columns
    cols = ["sharpe","max_dd","win_rate","turnover"]
    return df[cols]

def run_hpo(strategy_key: str, data: pd.DataFrame = None, n_trials: int = 50, metric: str = "sharpe"):
    data = data if data is not None else _load_fixture()
    hpo = HPOEngine(metric=metric)
    study = hpo.optimize(strategy_key, data, n_trials=n_trials)
    return {"best_value": study.best_value, "best_params": study.best_params, "trials": len(study.trials)}

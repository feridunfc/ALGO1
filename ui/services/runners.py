import uuid
import pandas as pd
from ...src.backtest.wf_runner import WalkForwardAdapter, BacktestEngine
from ...src.backtest.risk_execution_adapter import RiskExecutionAdapter
from ...src.strategies.ai_strategy import AIStrategy
from ...src.experiments.tracking_v2 import start_run, log_metrics, end_run

def _load_demo_data() -> pd.DataFrame:
    return pd.read_csv("tests/fixtures/golden_sample.csv", parse_dates=["timestamp"], index_col="timestamp")

def run_single():
    data = _load_demo_data()
    run_id = f"single-{uuid.uuid4().hex[:8]}"
    start_run(run_id, tag="single", params={"strategy": "AIStrategy"})
    strat = AIStrategy()
    eng = RiskExecutionAdapter()  # enforce risk chain
    res = eng.run(data=data, strategy=strat)
    # Best-effort metrics extraction
    try:
        eq = getattr(res, "equity_curve", None)
        sharpe = float((eq.pct_change().mean() / (eq.pct_change().std(ddof=0)+1e-12)) * (252**0.5)) if eq is not None else 0.0
        log_metrics(run_id, {"sharpe": sharpe})
    except Exception:
        pass
    end_run(run_id)
    return res

def run_walk_forward(n_splits=5, test_size=63, gap=1, strategy=None):
    data = _load_demo_data()
    run_id = f"wf-{uuid.uuid4().hex[:8]}"
    start_run(run_id, tag="wf", params={"n_splits": n_splits, "test_size": test_size, "gap": gap})
    wf = WalkForwardAdapter(BacktestEngine())
    strat = strategy or AIStrategy()
    res = wf.run(data=data, strategy=strat, n_splits=n_splits, test_size=test_size, gap=gap)
    try:
        agg = res.aggregate()
        log_metrics(run_id, agg)
    except Exception:
        pass
    end_run(run_id)
    return res

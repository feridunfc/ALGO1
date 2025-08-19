
from src.live.paper_engine import PaperExecutionSimulator

def test_paper_engine_exec():
    eng = PaperExecutionSimulator(initial_balance=1000.0, commission_bps=10)
    ok = eng.submit_order('AAPL', 'BUY', 1, 100.0, slippage_bps=5.0)
    assert ok
    assert eng.cash < 1000.0
    ok2 = eng.submit_order('AAPL', 'SELL', 1, 101.0, slippage_bps=5.0)
    assert ok2
    assert len(eng.fills) == 2

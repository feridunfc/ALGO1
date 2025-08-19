import pandas as pd
from src.core.backtest import BacktestEngine
from src.core.risk import RiskManager
from src.core.threshold_strategy import ThresholdSignalStrategy

def test_backtest_run():
    idx = pd.date_range('2023-01-01', periods=5, freq='D')
    df = pd.DataFrame({'open':[100,101,102,103,104],'close':[101,102,103,104,105]}, index=idx)
    df['score'] = [0.1,0.2,0.6,0.2,0.1]
    strat = ThresholdSignalStrategy(score_col='score', entry_thr=0.5, exit_thr=0.4, size=1)
    engine = BacktestEngine(df, initial_capital=1000, fees_bps=0.0, slippage_bps=0.0, one_bar_delay=True)
    rm = RiskManager({'max_drawdown':0.9})
    res = engine.run(strat, rm)
    assert 'final_equity' in res
    assert isinstance(res.get('transactions'), list)

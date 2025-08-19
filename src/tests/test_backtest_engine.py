
# src/tests/test_backtest_engine.py
import pandas as pd
import numpy as np
from core.backtest_engine import BacktestEngine, OrderDirection, OrderType, PercentageCommissionModel, VolatilityProportionalSlippage

def _make_ohlcv(start="2022-01-03", periods=30, freq="B", seed=42):
    rng = pd.date_range(start=start, periods=periods, freq=freq)
    rs = np.random.RandomState(seed)
    px = 100 + rs.randn(periods).cumsum()
    high = px + rs.rand(periods) * 1.0
    low = px - rs.rand(periods) * 1.0
    vol = rs.randint(1000, 5000, size=periods)
    df = pd.DataFrame({"open": px, "high": high, "low": low, "close": px, "volume": vol}, index=rng)
    return df

def test_basic_run():
    prices = {"AAPL": _make_ohlcv(), "MSFT": _make_ohlcv()}
    engine = BacktestEngine(
        price_data=prices,
        initial_capital=100_000.0,
        commission_model=PercentageCommissionModel(0.0005, min_commission=1.0),
        slippage_model=VolatilityProportionalSlippage(0.0003),
        risk_free_rate=0.01,
    )
    # submit before run (ensure scheduling happens)
    first_date = list(prices["AAPL"].index)[0]
    engine.submit_order("AAPL", OrderDirection.LONG, 10, OrderType.MARKET, submission_date=first_date)

    report = engine.run(prices["AAPL"].index[0], prices["AAPL"].index[-1])
    assert "performance" in report and "trades" in report
    assert len(report["portfolio_history"]) > 0

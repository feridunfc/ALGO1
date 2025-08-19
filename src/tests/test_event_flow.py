from autonom_ed.core.bus.event_bus import event_bus
from autonom_ed.core.events.strategy_events import SignalDirection
from autonom_ed.core.events.backtest_events import BacktestRequested
from autonom_ed.services.data_service import DataService
from autonom_ed.services.feature_service import FeatureService
from autonom_ed.services.strategy_service import StrategyService
from autonom_ed.services.risk_service import RiskService
from autonom_ed.services.execution_service import ExecutionService
from autonom_ed.services.portfolio_service import PortfolioService
from autonom_ed.services.backtest_service import BacktestingService
from autonom_ed.services.reporting_service import ReportingService
from datetime import datetime

def test_integration_smoke():
    # init
    _ = DataService()
    _ = FeatureService(ma_fast=5, ma_slow=10)
    _ = StrategyService(strategy_name="sma_crossover", params={})
    _ = RiskService(target_vol_annual=0.15, max_dd=0.5)
    _ = ExecutionService()
    _ = PortfolioService(starting_equity=10000.0)
    _ = ReportingService()
    _ = BacktestingService()
    # fire
    event_bus.publish(BacktestRequested(
        source="pytest", timestamp=datetime.utcnow(),
        symbol="SPY", start="2020-01-01", end="2020-06-01", interval="1d",
        strategy_name="sma_crossover"
    ))
    assert True

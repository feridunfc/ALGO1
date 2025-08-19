
import logging
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(name)s | %(message)s')

from core.bus.event_bus import event_bus
from core.events.backtest_events import BacktestRequested
from services.data_service import DataService
from services.feature_service import FeatureService
from services.strategy_service import StrategyService
from services.risk_service import RiskService
from services.portfolio_service import PortfolioService
from services.backtest_service import BacktestingService
from reporting.reporting_service import ReportingService

def main():
    # Initialize services (subscribe to events)
    _ = DataService()
    _ = FeatureService(sma_fast=20, sma_slow=50)   # can be made dynamic
    _ = StrategyService(name="ma_crossover")
    _ = RiskService(gross_cap=1.0)
    _ = PortfolioService(start_equity=1_000_000.0)
    _ = BacktestingService()
    _ = ReportingService()

    # Kick-off
    event_bus.publish(BacktestRequested(
        source="MainRunner",
        symbol="SPY",
        start="2018-01-01",
        end="2024-12-31",
        interval="1d",
        strategy="ma_crossover",
        params={"sma_fast":20, "sma_slow":50}
    ))

if __name__ == "__main__":
    main()

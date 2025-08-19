from core.event_bus import event_bus
from core.events import BacktestRequested, BarDataEvent
from services.backtesting_service import BacktestingService
from services.feature_service import FeatureService
from services.strategy_service import StrategyService
from services.risk_service import RiskService
from services.execution_service import ExecutionService
from services.portfolio_service import PortfolioService
from reporting.reporting_service import ReportingService

def run_event_backtest(symbol="SPY"):
    _ = BacktestingService()
    _ = FeatureService()
    _ = StrategyService()
    _ = RiskService()
    _ = ExecutionService()
    _ = PortfolioService()
    _ = ReportingService()

    event_bus.publish(BacktestRequested(
        source="main", symbol=symbol, start=None, end=None, interval="1d",
        wf_train=252, wf_test=63, mode="walkforward"
    ))

if __name__ == "__main__":
    run_event_backtest("SPY")
    print("\nDone.")

from __future__ import annotations
from autonom_ed.core.bus.event_bus import event_bus
from autonom_ed.core.events.backtest_events import BacktestRequested
from autonom_ed.configs.main_config import AppConfig
from autonom_ed.services.backtest_service import BacktestingService
from autonom_ed.services.feature_service import FeatureService
from autonom_ed.services.strategy_service import StrategyService
from autonom_ed.services.risk_service import RiskService
from autonom_ed.services.execution_service import ExecutionService
from autonom_ed.services.portfolio_service import PortfolioService
from autonom_ed.reporting.reporting_service import ReportingService

def run(cfg: AppConfig):
    # wire services
    _ = BacktestingService()
    _ = FeatureService(cfg.features)
    strat_params = {}
    for name in cfg.strategies.strategy_names:
        if name == "sma_crossover":
            strat_params[name] = {"fast": cfg.features.sma_fast, "slow": cfg.features.sma_slow}
        elif name == "rsi_threshold":
            strat_params[name] = {"rsi_period": cfg.features.rsi_period, "low": 30.0, "high": 70.0}
        elif name == "ai_logreg":
            strat_params[name] = {}
        elif name == "ai_random_forest":
            strat_params[name] = {}
    _ = StrategyService(strat_params)
    risk = RiskService(cfg.risk)
    exe = ExecutionService(fee_bps=cfg.fees.commission*10000, slippage_bps=cfg.fees.slippage_bps)
    port = PortfolioService(initial_cash=cfg.risk.initial_cash)
    _ = ReportingService()

    # connect portfolio -> risk/exe feedback
    def on_portfolio_update(event):
        risk.update_equity(event.total_value)
        exe.update_portfolio_value(event.total_value)
    from autonom_ed.core.events.order_portfolio_events import PortfolioUpdated
    event_bus.subscribe(PortfolioUpdated, on_portfolio_update)

    # fire backtest
    event_bus.publish(BacktestRequested(
        source="run_backtest",
        symbol=cfg.data.symbol,
        start=cfg.data.start,
        end=cfg.data.end,
        interval=cfg.data.interval,
        strategy_names=cfg.strategies.strategy_names,
        mode="simple"
    ))

if __name__ == "__main__":
    cfg = AppConfig()
    run(cfg)
    print("Backtest requested.")

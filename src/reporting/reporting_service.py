
import logging
import pandas as pd
from core.bus.event_bus import event_bus
from core.events.portfolio_events import PortfolioUpdated
from core.events.backtest_events import BacktestCompleted
from engines.metrics_engine import MetricsEngine

logger = logging.getLogger("ReportingService")

class ReportingService:
    def __init__(self, risk_free=0.0):
        self.bus = event_bus
        self.history = []
        self.bus.subscribe(PortfolioUpdated, self.on_portfolio)
        self.bus.subscribe(BacktestCompleted, self.on_complete)
        self.me = MetricsEngine(rf=risk_free)
        logger.info("ReportingService initialized.")

    def on_portfolio(self, e: PortfolioUpdated):
        self.history.append({'timestamp': e.timestamp, 'equity': e.total_value})

    def on_complete(self, e: BacktestCompleted):
        if not self.history:
            logger.warning("No portfolio history to report.")
            return
        df = pd.DataFrame(self.history).set_index('timestamp').sort_index()
        ret = df['equity'].pct_change().fillna(0.0)
        metrics = self.me.compute(df['equity'], ret)
        logger.info(f"REPORT {e.asset_name} {e.strategy_name}: {metrics}")
        # Store summary back into event for UI to fetch if needed
        e.summary = {'metrics': metrics, 'n_points': int(len(df))}
        # Reset for next run
        self.history = []

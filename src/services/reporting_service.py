
import pandas as pd
from ..core.bus.event_bus import event_bus
from ..core.events.portfolio_events import PortfolioUpdated
from ..core.events.backtest_events import BacktestCompleted
from ..engines.metrics_engine import compute_metrics

class ReportingService:
    def __init__(self):
        self.rows = []
        self.last_results = None
        event_bus.subscribe(PortfolioUpdated, self.on_portfolio)
        event_bus.subscribe(BacktestCompleted, self.on_done)

    def on_portfolio(self, e: PortfolioUpdated):
        self.rows.append({"timestamp":e.timestamp, "equity":e.equity, "weight":e.weight, "drawdown":e.drawdown})

    def on_done(self, e: BacktestCompleted):
        if not self.rows:
            self.last_results = (pd.DataFrame(), {})
            return
        df = pd.DataFrame(self.rows).set_index("timestamp").sort_index()
        metrics = compute_metrics(df["equity"])
        self.last_results = (df, metrics)
        self.rows = []

    def get_last_results(self):
        return self.last_results or (pd.DataFrame(), {})

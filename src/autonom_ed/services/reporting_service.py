from datetime import datetime
import pandas as pd
from pathlib import Path
from ..core.bus.event_bus import event_bus
from ..core.events.portfolio_events import PortfolioUpdated
from ..core.events.backtest_events import BacktestCompleted
from ..engines.metrics_engine import summarize

class ReportingService:
    def __init__(self, outdir="out"):
        self.bus = event_bus
        self.data = []
        self.meta = {}
        self.outdir = Path(outdir)
        self.outdir.mkdir(parents=True, exist_ok=True)
        self.bus.subscribe(PortfolioUpdated, self.on_portfolio)
        self.bus.subscribe(BacktestCompleted, self.on_done)

    def on_portfolio(self, event: PortfolioUpdated):
        self.data.append({"timestamp": event.timestamp, "equity": event.equity})

    def on_done(self, event: BacktestCompleted):
        if not self.data:
            print("No portfolio history recorded.")
            return
        df = pd.DataFrame(self.data).set_index("timestamp").sort_index()
        m = summarize(df["equity"])
        # Persist
        eq_path = self.outdir / f"equity_{event.symbol}_{event.strategy_name}.csv"
        mt_path = self.outdir / f"metrics_{event.symbol}_{event.strategy_name}.csv"
        df.to_csv(eq_path)
        pd.DataFrame([m]).to_csv(mt_path, index=False)
        print(f"[Reporting] Equity -> {eq_path}")
        print(f"[Reporting] Metrics -> {mt_path}")
        # reset
        self.data = []

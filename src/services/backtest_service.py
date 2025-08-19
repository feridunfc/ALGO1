
import logging
from core.bus.event_bus import event_bus
from core.events.backtest_events import BacktestRequested, BacktestCompleted
from core.events.data_events import BarDataEvent
from services.feature_service import FeatureService
from services.strategy_service import StrategyService
from services.risk_service import RiskService
from services.execution_service import ExecutionService
from services.portfolio_service import PortfolioService
from reporting.reporting_service import ReportingService
from utils.windows import WalkForwardConfig, generate_walkforward_slices

logger = logging.getLogger("BacktestingService")

class BacktestingService:
    def __init__(self):
        self.bus = event_bus
        self.bus.subscribe(BacktestRequested, self.on_backtest)

    def on_backtest(self, e: BacktestRequested):
        df = e.df.copy()
        df = df.sort_index()
        wf = e.wf_cfg or WalkForwardConfig()
        feature_cfg = e.feature_cfg or {}

        # Wire services
        feat = FeatureService(feature_cfg=feature_cfg)
        strat = StrategyService(strategy_name=e.strategy_name)
        risk = RiskService()
        exe = ExecutionService()
        port = PortfolioService()
        rep = ReportingService()

        # Walk-forward replay
        for i, (train_idx, test_idx) in enumerate(generate_walkforward_slices(df, wf)):
            # training window
            feat.reset(in_sample=True, symbol=e.asset_name)
            for idx in train_idx:
                row = df.loc[idx]
                self.bus.publish(BarDataEvent(
                    source=f"Backtest/train/{i}",
                    symbol=e.asset_name,
                    open=float(row['open']), high=float(row['high']), low=float(row['low']),
                    close=float(row['close']), volume=float(row['volume']),
                    index=idx
                ))
                # portfolio marks to keep equity updated
                port.mark_price(e.asset_name, float(row['close']))

            # testing window
            feat.reset(in_sample=False, symbol=e.asset_name)
            for idx in test_idx:
                row = df.loc[idx]
                self.bus.publish(BarDataEvent(
                    source=f"Backtest/test/{i}",
                    symbol=e.asset_name,
                    open=float(row['open']), high=float(row['high']), low=float(row['low']),
                    close=float(row['close']), volume=float(row['volume']),
                    index=idx
                ))
                port.mark_price(e.asset_name, float(row['close']))

        # end
        self.bus.publish(BacktestCompleted(
            source="BacktestReplay",
            asset_name=e.asset_name,
            strategy_name=e.strategy_name,
            summary=None
        ))
        logger.info("Backtest completed.")

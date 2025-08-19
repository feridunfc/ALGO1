from datetime import datetime
from ..core.bus.event_bus import event_bus
from ..core.events.strategy_events import StrategySignalGenerated
from ..core.events.risk_events import RiskAssessmentCompleted
from ..core.events.portfolio_events import PortfolioUpdated
from ..engines.risk_manager_engine import RiskManagerEngine

class RiskService:
    def __init__(self, target_vol_annual=0.15, max_dd=0.25):
        self.bus = event_bus
        self.engine = RiskManagerEngine(target_vol_annual=target_vol_annual, max_dd=max_dd)
        self.last_return = 0.0
        self.bus.subscribe(StrategySignalGenerated, self.on_signal)
        self.bus.subscribe(PortfolioUpdated, self.on_portfolio)

    def on_portfolio(self, event: PortfolioUpdated):
        self.engine.update_equity(event.equity)
        # the daily return used to update realized vol is event.meta? we can compute in PortfolioService

    def on_signal(self, event: StrategySignalGenerated):
        feats = event.meta.get("features", {}) if event.meta else {}
        daily_ret = float(feats.get("ret1", 0.0))
        target_w = self.engine.decide_weight(int(event.direction), daily_ret)
        rationale = f"vol_target with daily_ret={daily_ret:.5f}"
        self.bus.publish(RiskAssessmentCompleted(
            source="RiskService", timestamp=event.timestamp,
            symbol=event.symbol, direction=event.direction,
            target_weight=target_w, rationale=rationale
        ))


import logging
from core.bus.event_bus import event_bus
from core.events.strategy_events import StrategySignalGenerated, SignalDirection
from core.events.risk_events import RiskAssessmentCompleted
from risk.adaptive_drawdown_manager import AdaptiveDrawdownManager

logger = logging.getLogger("RiskService")

class RiskService:
    def __init__(self, start_cash=100_000.0, max_position_weight_pct=0.10):
        self.bus = event_bus
        self.dd = AdaptiveDrawdownManager()
        self.cash = start_cash
        self.portfolio_value = start_cash
        self.max_w = max_position_weight_pct
        self.bus.subscribe(StrategySignalGenerated, self.on_signal)
        logger.info("RiskService initialized.")

    def update_equity(self, total_value: float, realized_vol: float = 0.0):
        self.portfolio_value = total_value
        self.dd.update_threshold(volatility=realized_vol)

    def on_signal(self, e: StrategySignalGenerated):
        if e.direction == SignalDirection.HOLD:
            return
        # drawdown check
        if self.dd.check_drawdown(self.portfolio_value):
            logger.warning("Trade blocked by adaptive drawdown manager.")
            return
        # naive sizing: cap by max position weight
        dollar = self.portfolio_value * self.max_w * abs(e.strength)
        qty = 0.0
        if e.price > 0:
            qty = dollar / e.price
        self.bus.publish(RiskAssessmentCompleted(
            source="RiskService",
            symbol=e.symbol,
            direction=e.direction,
            quantity=qty,
            price=e.price,
            rationale=f"strength={e.strength:.2f}, cap={self.max_w:.2f}"
        ))


import logging
from core.bus.event_bus import event_bus
from core.events.risk_events import RiskAssessmentCompleted
from core.events.order_events import OrderFilled
from core.events.strategy_events import SignalDirection

logger = logging.getLogger("ExecutionService")

class ExecutionService:
    def __init__(self, slippage_bps=2.0):
        self.bus = event_bus
        self.slip = slippage_bps / 1e4
        self.bus.subscribe(RiskAssessmentCompleted, self.on_decision)
        logger.info("ExecutionService initialized.")

    def on_decision(self, e: RiskAssessmentCompleted):
        if e.quantity <= 0:
            return
        price = e.price * (1 + self.slip * (1 if e.direction==SignalDirection.LONG else -1))
        self.bus.publish(OrderFilled(
            source="ExecutionService",
            symbol=e.symbol,
            direction=e.direction,
            quantity=e.quantity,
            fill_price=price
        ))

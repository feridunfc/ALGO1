from datetime import datetime
from ..core.bus.event_bus import event_bus
from ..core.events.risk_events import RiskAssessmentCompleted
from ..core.events.order_events import OrderFilled
from ..core.events.data_events import BarDataEvent
from ..engines.execution_engine import ExecutionEngine

class ExecutionService:
    def __init__(self):
        self.bus = event_bus
        self.engine = ExecutionEngine()
        self.bus.subscribe(RiskAssessmentCompleted, self.on_decision)
        self.bus.subscribe(BarDataEvent, self.on_bar)

    def on_bar(self, event: BarDataEvent):
        self.engine.on_price(event.close)

    def on_decision(self, event: RiskAssessmentCompleted):
        # instant paper fill
        res = self.engine.execute_immediate(event.target_weight)
        self.bus.publish(OrderFilled(
            source="ExecutionService", timestamp=event.timestamp,
            symbol=event.symbol, price=res["price"],
            target_weight=res["target_weight"], direction=event.direction
        ))

from datetime import datetime
from ..core.bus.event_bus import event_bus
from ..core.events.order_events import OrderFilled
from ..core.events.portfolio_events import PortfolioReset, PortfolioUpdated
from ..core.events.data_events import BarDataEvent
from ..engines.portfolio_manager_engine import PortfolioManagerEngine

class PortfolioService:
    def __init__(self, starting_equity=100000.0):
        self.bus = event_bus
        self.engine = PortfolioManagerEngine(starting_equity=starting_equity)
        self.bus.subscribe(OrderFilled, self.on_fill)
        self.bus.subscribe(BarDataEvent, self.on_bar)

        # reset at init
        self.bus.publish(PortfolioReset(source="PortfolioService", timestamp=datetime.utcnow(),
                                        starting_equity=starting_equity))

    def on_fill(self, event: OrderFilled):
        self.engine.set_target_weight(event.target_weight)

    def on_bar(self, event: BarDataEvent):
        # compute return vs last price if available
        if self.engine.last_price is None:
            self.engine.set_price(event.close)
            equity = self.engine.equity
        else:
            ret = event.close / self.engine.last_price - 1.0
            equity = self.engine.mark_to_market(ret)
            self.engine.set_price(event.close)

        self.bus.publish(PortfolioUpdated(
            source="PortfolioService", timestamp=event.timestamp,
            equity=self.engine.equity, position=self.engine.weight, price=event.close
        ))

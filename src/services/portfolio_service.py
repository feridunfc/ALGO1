
import logging
from collections import defaultdict
from core.bus.event_bus import event_bus
from core.events.order_events import OrderFilled
from core.events.portfolio_events import PortfolioUpdated

logger = logging.getLogger("PortfolioService")

class PortfolioService:
    def __init__(self, start_cash=100_000.0):
        self.bus = event_bus
        self.cash = start_cash
        self.positions = defaultdict(float)
        self.last_price = {}
        self.total_value = start_cash
        self.bus.subscribe(OrderFilled, self.on_fill)
        logger.info("PortfolioService initialized.")

    def mark_price(self, symbol: str, price: float):
        self.last_price[symbol] = price
        self._recalc()

    def on_fill(self, e: OrderFilled):
        side = 1 if e.direction.value > 0 else -1
        self.positions[e.symbol] += side * e.quantity
        self.cash -= side * e.quantity * e.fill_price
        self.last_price[e.symbol] = e.fill_price
        self._recalc()

    def _recalc(self):
        pos_val = sum(qty * self.last_price.get(sym, 0.0) for sym, qty in self.positions.items())
        self.total_value = self.cash + pos_val
        self.bus.publish(PortfolioUpdated(
            source="PortfolioService",
            cash=self.cash,
            total_value=self.total_value,
            positions=dict(self.positions)
        ))

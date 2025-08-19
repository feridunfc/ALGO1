
import asyncio
from dataclasses import dataclass

@dataclass
class Order:
    symbol: str
    side: str   # 'BUY'/'SELL'
    qty: float
    limit_price: float | None = None

@dataclass
class ExecutionReport:
    symbol: str
    side: str
    qty: float
    avg_price: float
    status: str  # 'FILLED'/'PARTIAL'/'REJECTED'

class ExchangeAPI:
    def __init__(self, session=None):
        self.session = session
    async def place_order(self, symbol, side, type, price, time_in_force):
        await asyncio.sleep(0.01)
        return {"status": "FILLED", "avg_price": price}

class AsyncExecutionEngine:
    def __init__(self, liquidity_threshold: float = 1e6):
        self.liquidity_threshold = liquidity_threshold

    async def _execute_twap(self, order: Order, slices: int = 5, interval_sec: float = 0.05) -> ExecutionReport:
        slice_qty = order.qty / slices
        prices = []
        filled = 0.0
        for i in range(slices):
            await asyncio.sleep(interval_sec)
            price = (order.limit_price or 0) * (1 + 0.0001 * i)
            prices.append(price)
            filled += slice_qty
        avg_price = sum(prices) / len(prices) if prices else (order.limit_price or 0)
        return ExecutionReport(order.symbol, order.side, filled, avg_price, "FILLED")

    async def execute(self, order: Order) -> ExecutionReport:
        try:
            if order.qty * (order.limit_price or 0.0) > self.liquidity_threshold:
                return await self._execute_twap(order)
            api = ExchangeAPI()
            resp = await api.place_order(order.symbol, order.side, "LIMIT", order.limit_price or 0.0, "GTC")
            return ExecutionReport(order.symbol, order.side, order.qty, resp["avg_price"], resp["status"])
        except Exception:
            # Retry once
            await asyncio.sleep(0.1)
            api = ExchangeAPI()
            resp = await api.place_order(order.symbol, order.side, "LIMIT", order.limit_price or 0.0, "GTC")
            return ExecutionReport(order.symbol, order.side, order.qty, resp["avg_price"], resp["status"])

from __future__ import annotations
import asyncio
import random
import logging

from src.core.events import OrderSubmitEvent, OrderFilledEvent
from src.execution.gateway import ExecutionGateway

logger = logging.getLogger("execution.backtest_gateway")


class BacktestExecutionGateway(ExecutionGateway):
    def __init__(self, commission_rate: float = 0.001, slippage_bps: float = 0.0005, latency_ms_mean: float = 5.0, seed: int = 42):
        self.commission_rate = commission_rate
        self.slippage_bps = slippage_bps
        self.latency_ms_mean = latency_ms_mean
        random.seed(seed)

    async def execute_order(self, order: OrderSubmitEvent) -> OrderFilledEvent:
        latency = max(1.0, random.gauss(self.latency_ms_mean, 1.0))
        await asyncio.sleep(latency / 1000.0)

        mid = 100.0 if order.price is None else order.price
        slip = random.uniform(-self.slippage_bps, self.slippage_bps)
        fill_price = mid * (1.0 + slip)

        commission = abs(order.quantity) * fill_price * self.commission_rate
        slippage = abs(fill_price - mid)

        filled = OrderFilledEvent(
            order_id=order.order_id,
            symbol=order.symbol,
            filled_quantity=order.quantity,
            fill_price=fill_price,
            commission=commission,
            slippage=slippage,
            latency_ms=latency
        )
        return filled

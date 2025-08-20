from __future__ import annotations
import asyncio
from typing import List, Optional, Dict, Any
import pandas as pd
from datetime import datetime
import logging

from src.core.event_bus import EnhancedEventBus
from src.core.events import BarClosedEvent, OrderSubmitEvent, OrderFilledEvent, PortfolioEvent, EventTopic
from src.core.payload_store import PayloadStore

logger = logging.getLogger("core.backtest_engine")


class EventDrivenBacktestEngine:
    """
    Event-driven backtest engine with simple 1-bar delayed execution and portfolio accounting.
    Exposes:
      - equity_curve: List[tuple(timestamp, equity_value)]
      - trade_log: List[dict]
    """
    def __init__(self, event_bus: EnhancedEventBus, payload_store: PayloadStore, config: Optional[Dict[str, Any]] = None):
        self.event_bus = event_bus
        self.payload_store = payload_store
        self.config = config or {}
        self.execution_gateway = None  # attach via attach_execution()
        self.initial_capital = float(self.config.get("initial_capital", 100000.0))
        self.commission = float(self.config.get("commission", 0.001))
        self.slippage = float(self.config.get("slippage", 0.0))
        self._pending_orders: List[OrderSubmitEvent] = []
        self.positions: Dict[str, float] = {}
        self.cash: float = self.initial_capital
        self.equity_curve: List[tuple] = []
        self.trade_log: List[Dict[str, Any]] = []

    def attach_execution(self, gateway):
        self.execution_gateway = gateway

    async def run(self, data: pd.DataFrame, speed: float = 1.0):
        await self.event_bus.start()
        last_timestamp = None

        for _, row in data.iterrows():
            timestamp = row.get("timestamp", datetime.utcnow())
            bar_event = BarClosedEvent(
                symbol=row["symbol"],
                timeframe=self.config.get("timeframe", "1d"),
                open=float(row["open"]),
                high=float(row["high"]),
                low=float(row["low"]),
                close=float(row["close"]),
                volume=float(row["volume"]),
            )
            await self.event_bus.publish(EventTopic.BAR_CLOSED, bar_event)

            # Execute pending (1-bar delay)
            if self._pending_orders and self.execution_gateway:
                await self._flush_pending_orders(bar_event)

            # Update equity from latest close
            equity = self._mark_to_market(row["symbol"], float(row["close"]))
            self.equity_curve.append((timestamp, equity))
            await self.event_bus.publish(EventTopic.PORTFOLIO_UPDATE, PortfolioEvent(
                total_value=equity, cash=self.cash, leverage=self._leverage(), topic=EventTopic.PORTFOLIO_UPDATE
            ))

            last_timestamp = timestamp
            await asyncio.sleep(0)

        # drain remaining orders on final bar if any (optional)

    async def submit_order(self, order: OrderSubmitEvent):
        self._pending_orders.append(order)

    async def _flush_pending_orders(self, bar_event: BarClosedEvent):
        orders = list(self._pending_orders)
        self._pending_orders.clear()
        for ord_ev in orders:
            try:
                if self.execution_gateway is None:
                    logger.warning("No execution gateway attached; dropping order %s", ord_ev.order_id)
                    continue
                filled: OrderFilledEvent = await self.execution_gateway.execute_order(ord_ev)
                # Update portfolio
                self._apply_fill(filled)
                # Log trade
                self.trade_log.append({
                    "timestamp": bar_event.timestamp,
                    "symbol": filled.symbol,
                    "quantity": filled.filled_quantity,
                    "price": filled.fill_price,
                    "commission": filled.commission,
                    "slippage": filled.slippage,
                })
                # Publish ORDER_FILLED
                await self.event_bus.publish(EventTopic.ORDER_FILLED, filled)
            except Exception:
                logger.exception("Execution gateway failed for order %s", ord_ev.order_id)

    def _apply_fill(self, filled: OrderFilledEvent):
        qty = float(filled.filled_quantity)
        price = float(filled.fill_price)
        self.cash -= qty * price + float(filled.commission)
        self.positions[filled.symbol] = self.positions.get(filled.symbol, 0.0) + qty

    def _mark_to_market(self, symbol: str, close_price: float) -> float:
        pos = self.positions.get(symbol, 0.0)
        return self.cash + pos * close_price

    def _leverage(self) -> float:
        exposure = sum(abs(q) for q in self.positions.values())
        return 0.0 if self.initial_capital == 0 else exposure / self.initial_capital

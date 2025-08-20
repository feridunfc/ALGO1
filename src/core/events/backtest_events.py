from __future__ import annotations
from pydantic import Field
from .base_event import BaseEvent, EventTopic

class BarClosedEvent(BaseEvent):
    topic: EventTopic = Field(default=EventTopic.BAR_CLOSED)
    symbol: str
    timeframe: str
    open: float
    high: float
    low: float
    close: float
    volume: float

class OrderSubmitEvent(BaseEvent):
    topic: EventTopic = Field(default=EventTopic.ORDER_SUBMIT)
    order_id: str
    symbol: str
    side: int               # 1 buy, -1 sell
    quantity: float
    price: float | None = None
    order_type: str = "market"

class OrderFilledEvent(BaseEvent):
    topic: EventTopic = Field(default=EventTopic.ORDER_FILLED)
    order_id: str
    symbol: str
    filled_quantity: float
    fill_price: float
    commission: float
    slippage: float
    latency_ms: float

class PortfolioEvent(BaseEvent):
    topic: EventTopic = Field(default=EventTopic.PORTFOLIO_UPDATE)
    total_value: float
    cash: float
    leverage: float

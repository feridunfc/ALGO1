from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum
import uuid

class EventTopic(str, Enum):
    TICK_DATA = "tick_data"
    BAR_CLOSED = "bar_closed"
    SIGNAL_GENERATED = "signal_generated"
    ORDER_SUBMIT = "order_submit"
    ORDER_FILLED = "order_filled"
    RISK_ALERT = "risk_alert"
    PORTFOLIO_UPDATE = "portfolio_update"
    METRIC_UPDATE = "metric_update"
    HEARTBEAT = "heartbeat"

class BaseEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    topic: EventTopic
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: str = "1.0.0"
    payload_ref: Optional[str] = None
    payload_summary: Optional[Dict[str, Any]] = None
    payload_digest: Optional[str] = None
    metadata: Dict[str, Any] = {}

    class Config:
        allow_mutation = False
        arbitrary_types_allowed = True

class BarClosedEvent(BaseEvent):
    topic: EventTopic = Field(default=EventTopic.BAR_CLOSED)
    symbol: str
    timeframe: str
    open: float
    high: float
    low: float
    close: float
    volume: float

class SignalEvent(BaseEvent):
    topic: EventTopic = Field(default=EventTopic.SIGNAL_GENERATED)
    strategy_id: str
    symbol: str
    direction: int  # 1 buy, -1 sell
    strength: float  # 0..1
    confidence: float  # 0..1
    target_size: Optional[float] = None

class OrderSubmitEvent(BaseEvent):
    topic: EventTopic = Field(default=EventTopic.ORDER_SUBMIT)
    order_id: str
    symbol: str
    side: int  # 1 buy, -1 sell
    quantity: float
    price: Optional[float] = None
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

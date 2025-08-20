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

    # ağır yükleri disk'e offload etmek için
    payload_ref: Optional[str] = None
    payload_summary: Optional[Dict[str, Any]] = None
    payload_digest: Optional[str] = None

    # serbest metadata
    metadata: Dict[str, Any] = {}

    class Config:
        arbitrary_types_allowed = True

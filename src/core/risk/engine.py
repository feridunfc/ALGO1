from __future__ import annotations
import asyncio
import logging
import uuid
from typing import Optional

from src.core.event_bus import EnhancedEventBus
from src.core.events import SignalEvent, OrderSubmitEvent, EventTopic

logger = logging.getLogger("core.risk_engine")

class RiskAssessment:
    def __init__(self, approved: bool, reason: Optional[str] = None, adjusted_size: Optional[float] = None):
        self.approved = approved
        self.reason = reason
        self.adjusted_size = adjusted_size

    @classmethod
    def approved_assessment(cls, size: float):
        return cls(True, None, size)

    @classmethod
    def rejected_assessment(cls, reason: str):
        return cls(False, reason, None)

class RiskEngine:
    def __init__(self, event_bus: Optional[EnhancedEventBus], config: Optional[dict] = None):
        self.event_bus = event_bus
        self.config = config or {}
        if self.event_bus is not None:
            self.event_bus.subscribe(EventTopic.SIGNAL_GENERATED, self._on_signal, is_async=True)

    async def _on_signal(self, event: SignalEvent):
        assessment = await self.assess_signal_risk(event)
        if assessment.approved:
            order = OrderSubmitEvent(
                order_id=str(uuid.uuid4()),
                symbol=event.symbol,
                side=event.direction,
                quantity=assessment.adjusted_size or 0.0,
                price=None,
            )
            await self.event_bus.publish(EventTopic.ORDER_SUBMIT, order)
        else:
            logger.info("Signal rejected by risk: %s", assessment.reason)

    async def assess_signal_risk(self, signal: SignalEvent) -> RiskAssessment:
        ps = self.config.get("position_sizing", {})
        base = float(ps.get("base_size", 1000.0))
        min_pos = float(ps.get("min_position", 1.0))
        size = max(min_pos, base * abs(float(signal.strength)))

        cons = self.config.get("constraints", {})
        max_pos = float(cons.get("max_position_size", 1e6))
        if size > max_pos:
            return RiskAssessment.rejected_assessment("exceeds max_position_size")

        if not await self._liquidity_ok(signal.symbol, size):
            return RiskAssessment.rejected_assessment("insufficient_liquidity")
        return RiskAssessment.approved_assessment(size)

    async def _liquidity_ok(self, symbol: str, size: float) -> bool:
        await asyncio.sleep(0)  # yield
        return True

from __future__ import annotations
import asyncio
import logging
from typing import Dict, Any, List

from src.core.event_bus import EnhancedEventBus
from src.core.events import BarClosedEvent, SignalEvent, EventTopic

logger = logging.getLogger("core.strategy_orchestrator")


class StrategyOrchestrator:
    def __init__(self, event_bus: EnhancedEventBus, risk_engine):
        self.event_bus = event_bus
        self.risk_engine = risk_engine
        self.strategies: Dict[str, Any] = {}
        self.event_bus.subscribe(EventTopic.BAR_CLOSED, self._on_bar_closed, is_async=True)

    async def _on_bar_closed(self, event: BarClosedEvent):
        tasks: List[asyncio.Task] = []
        for s in self.strategies.values():
            try:
                coro = s.on_bar(event)
                tasks.append(asyncio.create_task(coro))
            except Exception:
                logger.exception("Strategy on_bar direct call failed")
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for r in results:
                if isinstance(r, Exception):
                    logger.exception("Strategy task failed: %s", r)
                    continue
                signals = r or []
                for sig in signals:
                    if not isinstance(sig, SignalEvent):
                        logger.warning("Non-SignalEvent produced: %s", type(sig))
                        continue
                    await self.event_bus.publish(EventTopic.SIGNAL_GENERATED, sig)

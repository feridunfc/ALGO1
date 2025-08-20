from __future__ import annotations
from abc import ABC, abstractmethod
from src.core.events import OrderSubmitEvent, OrderFilledEvent

class ExecutionGateway(ABC):
    @abstractmethod
    async def execute_order(self, order: OrderSubmitEvent) -> OrderFilledEvent:
        raise NotImplementedError

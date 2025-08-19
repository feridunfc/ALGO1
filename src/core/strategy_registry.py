from typing import Dict, Type
import inspect, logging
logger = logging.getLogger(__name__)

class StrategyRegistry:
    _strategies: Dict[str, Type] = {}

    @classmethod
    def register(cls, name: str):
        def decorator(strategy_cls: Type):
            if not inspect.isclass(strategy_cls):
                raise ValueError("Only classes can be registered as strategies")
            if name in cls._strategies:
                logger.warning("Overwriting strategy '%s' in registry", name)
            cls._strategies[name] = strategy_cls
            return strategy_cls
        return decorator

    @classmethod
    def get(cls, name: str, **kwargs):
        if name not in cls._strategies:
            raise KeyError(name)
        return cls._strategies[name](**kwargs)

    @classmethod
    def list(cls):
        return dict(cls._strategies)

from abc import ABC, abstractmethod
class StrategyBase(ABC):
    name = 'base_strategy'
    def __init__(self):
        pass

    @abstractmethod
    def fit(self, X, y=None):
        pass

    @abstractmethod
    def generate_signal(self, timestamp, row):
        pass

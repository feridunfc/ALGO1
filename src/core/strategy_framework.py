from abc import ABC, abstractmethod
import pandas as pd, numpy as np
from typing import Dict, Any, Type

class StrategyBase(ABC):
    def __init__(self, config: Dict=None):
        self.config = config or {'entry_threshold':0.5, 'exit_threshold':0.3, 'lookback_window':21}
        self.name = self.__class__.__name__

    @abstractmethod
    def generate_signals(self, data: pd.DataFrame)->pd.Series:
        pass

class StrategyRegistry:
    def __init__(self):
        self._strategies = {}

    def register(self, name: str, cls: Type[StrategyBase]):
        if not issubclass(cls, StrategyBase):
            raise TypeError('Must subclass StrategyBase')
        self._strategies[name] = cls

    def create_ensemble(self, strategy_weights: Dict[str,float], configs: Dict[str,Dict]=None):
        return StrategyEnsemble(strategy_weights, self._strategies, configs or {})

class StrategyEnsemble(StrategyBase):
    def __init__(self, strategy_weights, strategy_classes, strategy_configs):
        super().__init__()
        self.weights = strategy_weights
        self.strategies = {name: cls(strategy_configs.get(name,{})) for name, cls in strategy_classes.items() if name in strategy_weights}

    def generate_signals(self, data: pd.DataFrame)->pd.Series:
        df = pd.DataFrame(index=data.index)
        for name, strat in self.strategies.items():
            df[name] = strat.generate_signals(data)
        w = pd.Series(self.weights)
        return df.dot(w)

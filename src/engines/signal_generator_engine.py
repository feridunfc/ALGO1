from __future__ import annotations
import pandas as pd
from typing import Dict, List
from ..strategies.strategy_factory import create, registered, BaseStrategy

class SignalGeneratorEngine:
    def __init__(self, strategy_params: Dict[str, dict]):
        # instantiate strategies based on provided params
        self.strategies: Dict[str, BaseStrategy] = {}
        for name, params in strategy_params.items():
            self.strategies[name] = create(name, **params)

    def ensure_trained(self, name: str, features_df: pd.DataFrame):
        strat = self.strategies[name]
        if not strat.is_trained:
            strat.train(features_df)

    def signal_for_bar(self, name: str, features_df: pd.DataFrame) -> int:
        strat = self.strategies[name]
        # For per-bar decision, pass the full features but use last decision
        sig_series = strat.predict(features_df.tail(300))  # small window to speed up
        return int(sig_series.iloc[-1])

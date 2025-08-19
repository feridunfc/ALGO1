from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class DataConfig:
    source: str = "yfinance"
    symbol: str = "SPY"
    start: Optional[str] = "2018-01-01"
    end: Optional[str] = None
    interval: str = "1d"

@dataclass
class FeesConfig:
    commission: float = 0.0002  # 2 bps
    slippage_bps: float = 5.0

@dataclass
class RiskConfig:
    initial_cash: float = 100000.0
    max_weight_per_asset: float = 0.3
    risk_per_trade_pct: float = 0.01
    atr_multiplier: float = 2.0
    vol_target_annual: float = 0.15
    max_drawdown_limit: float = 0.3  # stop trading when breached

@dataclass
class FeatureConfig:
    sma_fast: int = 20
    sma_slow: int = 50
    rsi_period: int = 14
    vol_window: int = 30

@dataclass
class StrategyParams:
    # declared strategies to run
    strategy_names: List[str] = field(default_factory=lambda: ["sma_crossover"])

@dataclass
class AppConfig:
    data: DataConfig = field(default_factory=DataConfig)
    fees: FeesConfig = field(default_factory=FeesConfig)
    risk: RiskConfig = field(default_factory=RiskConfig)
    features: FeatureConfig = field(default_factory=FeatureConfig)
    strategies: StrategyParams = field(default_factory=StrategyParams)

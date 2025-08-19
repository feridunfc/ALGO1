
from dataclasses import dataclass

@dataclass
class DataConfig:
    source: str = "yfinance"
    symbol: str = "SPY"
    start: str = "2015-01-01"
    end: str | None = None
    interval: str = "1d"

@dataclass
class FeesConfig:
    commission: float = 0.0
    slippage_bps: float = 0.0

@dataclass
class RiskConfig:
    target_vol: float = 0.15
    max_dd_pct: float = 0.3
    vol_window: int = 20
    max_leverage: float = 1.0

@dataclass
class AppConfig:
    data: DataConfig = DataConfig()
    fees: FeesConfig = FeesConfig()
    risk: RiskConfig = RiskConfig()
    strategy_name: str = "sma_crossover"
    params: dict | None = None

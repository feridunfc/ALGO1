from dataclasses import dataclass, field
from typing import Optional, List

@dataclass
class DataConfig:
    source: str = "yfinance"
    symbol: str = "SPY"
    start: str = "2015-01-01"
    end: Optional[str] = None
    interval: str = "1d"
    csv_path: Optional[str] = None
    parquet_path: Optional[str] = None
    auto_adjust: bool = True
    tz: Optional[str] = None

@dataclass
class FeesConfig:
    commission: float = 0.0005
    slippage_bps: float = 1.0

@dataclass
class RiskConfig:
    target_annual_vol: float = 0.20
    lookback_days: int = 30
    max_position_weight_pct: float = 0.10
    max_drawdown_cap: float = 0.20

@dataclass
class BacktestConfig:
    walkforward_splits: int = 1
    threshold: float = 0.5
    seed: int = 42

@dataclass
class UIConfig:
    default_models: List[str] = field(default_factory=lambda: ["random_forest"])
    default_strategies: List[str] = field(default_factory=lambda: ["ma_crossover"])

@dataclass
class AppConfig:
    data: DataConfig = field(default_factory=DataConfig)
    fees: FeesConfig = field(default_factory=FeesConfig)
    risk: RiskConfig = field(default_factory=RiskConfig)
    bt: BacktestConfig = field(default_factory=BacktestConfig)
    ui: UIConfig = field(default_factory=UIConfig)

def load_config() -> AppConfig:
    return AppConfig()

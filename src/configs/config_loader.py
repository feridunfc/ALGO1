
from .config_dataclasses import AppConfig, DataConfig, FeesConfig, RiskConfig

DEFAULT = AppConfig(
    data=DataConfig(),
    fees=FeesConfig(),
    risk=RiskConfig(),
    strategy_name="sma_crossover",
    params={"ma_fast":20,"ma_slow":50},
)

def load_config_from_yaml(path: str | None = None) -> AppConfig:
    return DEFAULT

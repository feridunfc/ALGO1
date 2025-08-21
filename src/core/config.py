# src/core/config.py
from dataclasses import dataclass
from typing import Literal, Optional

from dataclasses import dataclass, field
from typing import Optional, List

from pathlib import Path

class Config:
    # Kütüphane bayrakları
    SKLEARN_AVAILABLE = True
    OPTUNA_AVAILABLE = False
    IMBLEARN_AVAILABLE = False

    # Eğitim/kayıt yolu
    PROJECT_ROOT_PATH = Path(".")
    MODEL_SAVE_DIR = PROJECT_ROOT_PATH / "saved_models"

    # Model default paramları (gerekirse genişletin)
    MODEL_PARAMS = {
        "random_forest": {},
        "extra_trees": {},
        "logistic": {},
        "svm": {},
        "knn": {},
        "naive_bayes": {},
        "lightgbm": {},
        "xgboost": {},
        "catboost": {},
        "lstm": {},
        "online_sgd": {},
    }

    # Optimizasyon ayarları (isteğe bağlı)
    OPTIMIZATION_PARAMS = {
        "enable_optimization": False,
        "cv_default_type": "timeseries",
        "cv_folds": 3,
        "scoring_metric": "f1_weighted",
    }

    # SMOTE ve sinyal eşiği varsayılanları (AI için)
    USE_SMOTE_SAMPLING = False
    AI_SIGNAL_PARAMS = {
        "buy_confidence_threshold": 0.55,
        "sell_confidence_threshold": 0.55,
        "confidence_gap_threshold": 0.10,
    }



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

NaNPolicy = Literal["drop", "ffill", "bfill", "interp", "fill_value"]
Scaler = Literal["none", "zscore", "minmax", "robust"]

@dataclass(frozen=True)
class NormalizationConfig:
    nan_policy: NaNPolicy = "ffill"
    fill_value: Optional[float] = None
    scaler: Scaler = "none"
    clip_outliers_z: Optional[float] = None
    tz: str = "UTC"
    ensure_monotonic: bool = True
    ensure_unique_index: bool = True

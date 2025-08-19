from __future__ import annotations
from typing import Dict, Type, List
import warnings

_REGISTRY: Dict[str, type] = {}

def register(name: str, cls: type):
    _REGISTRY[name.lower()] = cls

def get_model_registry() -> Dict[str, type]:
    return _REGISTRY

def list_models() -> List[str]:
    return sorted(_REGISTRY.keys())

# ----- RandomForest (required) -----
try:
    from .rf import RandomForestModel
    register("random_forest", RandomForestModel)
except Exception as e:
    warnings.warn(f"RandomForest registration failed: {e}")

# ----- XGBoost (optional) -----
try:
    from .xgb import XGBoostModel
    register("xgboost", XGBoostModel)
except Exception:
    # silently skip if xgboost not installed
    pass

# ----- LightGBM (optional) -----
try:
    from .lgbm import LightGBMModel
    register("lightgbm", LightGBMModel)
except Exception:
    pass
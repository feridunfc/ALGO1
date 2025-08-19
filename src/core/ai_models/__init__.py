from __future__ import annotations
from typing import Dict, Type, List, Optional
from importlib import import_module
import pkgutil, inspect

try:
    # aynı klasörde
    from .base_ai_model import BaseAIModel
except Exception:
    # Eski kurulumlar için: interface’i gevşek kontrol edeceğiz
    class BaseAIModel:  # type: ignore
        pass

# İsteğe bağlı ipuçları (modül.kls yolu)
_MODEL_HINTS = {
    "random_forest": "model_rf.RandomForestModel",
    "xgboost":       "model_xgb.XGBoostModel",     # varsa
    "tabnet":        "model_tabnet.TabNetModel",   # varsa
}

class AIModelRegistry:
    def __init__(self) -> None:
        self._models: Dict[str, Type[BaseAIModel]] = {}

    def register(self, name: str, model_class: Type[BaseAIModel]) -> None:
        self._models[name.lower()] = model_class

    def has_model(self, name: str) -> bool:
        return name.lower() in self._models

    def get_model(self, name: str) -> Type[BaseAIModel]:
        key = name.lower()
        if key not in self._models:
            raise ValueError(f"AI model not registered: {name}")
        return self._models[key]

    def list_models(self) -> List[str]:
        return sorted(self._models.keys())

registry = AIModelRegistry()

def _safe_import(path: str):
    try:
        return import_module(path)
    except Exception:
        return None

def _auto_discover() -> None:
    """
    Bu paket altındaki model_* modüllerini tarar ve BaseAIModel’den türeyen sınıfları kaydeder.
    """
    pkg_name = __name__  # 'core.strategies.ai_models'
    # 1) ipuçlarını dene
    for key, dotted in _MODEL_HINTS.items():
        try:
            mod_name, cls_name = dotted.rsplit(".", 1)
            mod = _safe_import(f"{pkg_name}.{mod_name}")
            if not mod:
                continue
            cls = getattr(mod, cls_name, None)
            if cls and inspect.isclass(cls):
                registry.register(key, cls)
        except Exception:
            pass

    # 2) model_*.py’leri tara
    try:
        for _, modname, ispkg in pkgutil.iter_modules(__path__):  # type: ignore # noqa
            if ispkg or not modname.startswith("model_"):
                continue
            mod = _safe_import(f"{pkg_name}.{modname}")
            if not mod:
                continue
            for attr, obj in inspect.getmembers(mod, inspect.isclass):
                # BaseAIModel alt sınıfı olsun
                try:
                    if obj is not BaseAIModel and issubclass(obj, BaseAIModel):
                        # İsim anahtarı: dosya ismi veya sınıf id’si
                        key = getattr(obj, "MODEL_ID", None)
                        if not key:
                            key = modname.replace("model_", "")
                        registry.register(str(key).lower(), obj)
                except Exception:
                    continue
    except Exception:
        pass

_auto_discover()

# Dış API
def list_models() -> List[str]:
    return registry.list_models()

def get_model(name: str) -> Type[BaseAIModel]:
    return registry.get_model(name)

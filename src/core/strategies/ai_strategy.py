# src/core/strategies/ai_models.py
from __future__ import annotations
from typing import List, Type

def list_models() -> List[str]:
    try:
        from core.ai_models import list_models as _lm
        return _lm()
    except Exception:
        ids = []
        try:
            from core.ai_models.model_rf import RandomForestModel  # noqa
            ids.append("random_forest")
        except Exception:
            pass
        try:
            from core.ai_models.model_tabnet import TabNetModel  # noqa
            ids.append("tabnet")
        except Exception:
            pass
        return ids

def get_model_class(name: str) -> Type:
    # mümkünse gerçek registry’den al
    try:
        from core.ai_models import get_model_class as _gm
        return _gm(name)
    except Exception:
        mapping = {}
        try:
            from core.ai_models.model_rf import RandomForestModel
            mapping["random_forest"] = RandomForestModel
        except Exception:
            pass
        try:
            from core.ai_models.model_tabnet import TabNetModel
            mapping["tabnet"] = TabNetModel
        except Exception:
            pass
        cls = mapping.get(name.lower())
        if not cls:
            raise ValueError(f"AI model not found: {name}")
        return cls

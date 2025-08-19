from __future__ import annotations
from typing import Dict, Type, Any, Callable

_MODEL_REGISTRY: Dict[str, Type] = {}

def register_model(name: str) -> Callable[[Type], Type]:
    def deco(cls: Type) -> Type:
        _MODEL_REGISTRY[name] = cls
        return cls
    return deco

def get_model(name: str, **kwargs) -> Any:
    if name not in _MODEL_REGISTRY:
        raise KeyError(f"Model '{name}' not found. Available: {list(_MODEL_REGISTRY.keys())}")
    return _MODEL_REGISTRY[name](**kwargs)

def list_models() -> list:
    return sorted(list(_MODEL_REGISTRY.keys()))
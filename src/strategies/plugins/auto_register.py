# src/strategies/plugins/auto_register.py
from __future__ import annotations
import importlib
import inspect
from typing import Optional, Union
from src.strategies.registry import register_strategy

def _import_from_spec(spec: str):
    modpath, _, clsname = spec.partition(":")
    if not modpath or not clsname:
        raise ValueError(f"Invalid spec '{spec}', expected 'pkg.mod:ClassName'")
    mod = importlib.import_module(modpath)
    return getattr(mod, clsname)

def try_register(a: Union[str, type], b: Optional[Union[str, type]] = None) -> bool:
    """
    Esnek kayıt:
      - try_register("key", "pkg.mod:Class")          # klasik
      - try_register("key", SomeStrategyClass)        # sınıf doğrudan
      - try_register(SomeStrategyClass, "key")        # argümanlar ters
      - try_register("pkg.mod:Class")                 # key=ClassName.lower() türetir
      - try_register(SomeStrategyClass)               # key=ClassName.lower()
    """
    try:
        # 2 argümanlı kullanım
        if b is not None:
            if isinstance(a, str) and isinstance(b, str):
                cls = _import_from_spec(b); key = a
            elif isinstance(a, str) and inspect.isclass(b):
                cls = b; key = a
            elif inspect.isclass(a) and isinstance(b, str):
                cls = a; key = b
            else:
                return False
        # 1 argümanlı kullanım
        else:
            if isinstance(a, str):
                cls = _import_from_spec(a)
                key = cls.__name__.lower()
            elif inspect.isclass(a):
                cls = a
                key = cls.__name__.lower()
            else:
                return False

        register_strategy(key)(cls)
        return True
    except Exception:
        return False

def bootstrap() -> int:
    """Opsiyonel auto-discovery kancası (şimdilik no-op)."""
    return 0

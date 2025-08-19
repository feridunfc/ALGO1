# src/strategies/plugins/auto_register.py
from __future__ import annotations
import importlib
import pkgutil
import pathlib
from typing import Optional

try:
    # ana registry
    from src.strategies.registry import STRATEGY_REGISTRY, register_strategy  # noqa: F401
except Exception:  # fallback: göreli import da çalışsın
    from ..registry import STRATEGY_REGISTRY, register_strategy  # type: ignore

def _iter_strategy_pkgs():
    """
    src/strategies altında ai/, conventional/, hybrid/ gibi alt paketleri dolaş.
    Her paket içindeki modülleri import ederek register() yan etkisini tetikle.
    """
    base = pathlib.Path(__file__).resolve().parents[1]  # .../src/strategies
    pkg_name = "src.strategies"
    for finder, modname, ispkg in pkgutil.walk_packages([str(base)], prefix=f"{pkg_name}."):
        yield modname

def _safe_import(modname: str) -> Optional[object]:
    try:
        return importlib.import_module(modname)
    except Exception:
        # Strateji modüllerinde opsiyonel bağımlılıklar olabilir; sessizce geç.
        return None

def bootstrap() -> int:
    """
    Tüm strateji modüllerini keşfedip import eder.
    Modüller import olunca, kendi içlerinde @register_strategy veya register() ile kayıt yaparlar.
    """
    before = len(STRATEGY_REGISTRY)
    for mod in _iter_strategy_pkgs():
        _safe_import(mod)
    after = len(STRATEGY_REGISTRY)
    return after - before

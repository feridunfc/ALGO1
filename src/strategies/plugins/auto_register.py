from __future__ import annotations
import importlib, pkgutil, inspect
from typing import Dict, Type

def bootstrap(verbose: bool = False) -> Dict[str, Type]:
    """
    Discover & register strategies into STRATEGY_REGISTRY.
    - Walks src.strategies.* packages
    - Adds any class subclassing `Strategy` to the registry if it exposes a `name` or __name__
    """
    try:
        from src.strategies.base import Strategy  # type: ignore
    except Exception as e:
        if verbose:
            print("[auto_register] base import failed:", e)
        return {}

    try:
        from src.strategies.registry import STRATEGY_REGISTRY  # type: ignore
    except Exception:
        # Fallback local registry if project doesn't expose one
        STRATEGY_REGISTRY = {}

    registered_before = set(STRATEGY_REGISTRY.keys())

    # Drill into package
    try:
        strategies_pkg = importlib.import_module("src.strategies")
    except Exception as e:
        if verbose:
            print("[auto_register] cannot import src.strategies:", e)
        return dict(STRATEGY_REGISTRY)

    for modinfo in pkgutil.walk_packages(
        strategies_pkg.__path__, strategies_pkg.__name__ + "."
    ):
        modname = modinfo.name
        # skip obvious non-strategy modules
        if any(skip in modname for skip in (".plugins", ".__", ".registry", ".base")):
            continue
        try:
            mod = importlib.import_module(modname)
        except Exception:
            # keep going; some optional deps may be missing
            continue

        for _, obj in inspect.getmembers(mod, inspect.isclass):
            if not issubclass(obj, Strategy) or obj is Strategy:
                continue
            # pick a registry key
            key = getattr(obj, "name", None) or obj.__name__
            key = str(key).strip()
            if not key:
                continue
            if key in STRATEGY_REGISTRY:
                continue
            STRATEGY_REGISTRY[key] = obj
            if verbose:
                print(f"[auto_register] registered: {key} -> {obj}")

    if verbose:
        newly = set(STRATEGY_REGISTRY.keys()) - registered_before
        print(f"[auto_register] total={len(STRATEGY_REGISTRY)} (+{len(newly)})")
    return dict(STRATEGY_REGISTRY)

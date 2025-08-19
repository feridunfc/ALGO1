
"""Auto-register plugin strategies into existing STRATEGY_REGISTRY if available."""
def try_register(name: str, cls):
    try:
        import src.strategies.registry as reg
        if hasattr(reg, "STRATEGY_REGISTRY"):
            reg.STRATEGY_REGISTRY[name] = cls
    except Exception:
        pass

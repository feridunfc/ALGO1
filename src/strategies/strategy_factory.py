
from .hybrid_v1 import HybridV1Strategy

REGISTRY = {
    "hybrid_v1": HybridV1Strategy,
}

def create(name: str, **kwargs):
    cls = REGISTRY.get(name)
    if cls is None:
        raise ValueError(f"Unknown strategy: {name}")
    return cls(**kwargs)

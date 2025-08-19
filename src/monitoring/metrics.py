from __future__ import annotations
from typing import Dict, Tuple, Any, Optional, List
import threading

class _Metric:
    def __init__(self, name: str, description: str = "", labels: Optional[List[str]] = None):
        self.name = name; self.description = description; self.labels = labels or []
        self._lock = threading.Lock(); self._samples: Dict[Tuple[Any, ...], float] = {}

    def _key(self, label_values: Dict[str, Any]) -> Tuple[Any, ...]:
        return tuple(label_values.get(k) for k in self.labels)

    def inc(self, value: float = 1.0, **label_values):
        with self._lock:
            k = self._key(label_values); self._samples[k] = self._samples.get(k, 0.0) + float(value)

    def export_prom(self) -> str:
        lines = [f"# TYPE {self.name} gauge"]
        with self._lock:
            for k, v in self._samples.items():
                if not self.labels:
                    lines.append(f"{self.name} {v}")
                else:
                    parts = []
                    for i, lab in enumerate(self.labels):
                        val = k[i] if i < len(k) else ""
                        parts.append(f'{lab}="{val}"')
                    lines.append(f"{self.name}{{{','.join(parts)}}} {v}")
        return "\n".join(lines)

class Registry:
    def __init__(self): self.metrics: Dict[str, _Metric] = {}
    def counter(self, name: str, description: str = "", labels: Optional[List[str]] = None) -> _Metric:
        if name not in self.metrics: self.metrics[name] = _Metric(name, description, labels)
        return self.metrics[name]
    def to_prometheus_text(self) -> str:
        return "\n".join([m.export_prom() for m in self.metrics.values()])

REGISTRY = Registry()

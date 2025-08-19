# src/config/settings.py
import os
from dataclasses import dataclass, field
from typing import Dict, Any

try:
    import yaml  # pip install PyYAML
except ImportError:
    yaml = None

def _load_yaml(path: str) -> dict:
    if not os.path.exists(path):
        return {}
    if yaml is None:
        # PyYAML yoksa en azından kırılma olmasın
        print(f"[WARN] PyYAML yüklü değil, {path} okunamadı (boş kabul ediliyor).")
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}

@dataclass
class Settings:
    env: str = os.getenv("APP_ENV", "dev")
    project_name: str = os.getenv("PROJECT_NAME", "ALGO-TRADE-SYSTEM")
    timezone: str = os.getenv("TZ", "UTC")
    exchanges: Dict[str, Any] = field(default_factory=dict)
    symbols_map: Dict[str, str] = field(default_factory=dict)
    features: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def load(cls, base_dir: str) -> "Settings":
        cfg = cls()
        cfg.exchanges   = _load_yaml(os.path.join(base_dir, "src", "config", "exchanges.yaml"))
        cfg.symbols_map = _load_yaml(os.path.join(base_dir, "src", "config", "symbols_map.yaml"))
        cfg.features    = _load_yaml(os.path.join(base_dir, "src", "config", "features.yaml"))
        return cfg

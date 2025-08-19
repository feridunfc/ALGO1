
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

@dataclass
class ApiKeys:
    api_key: str
    api_secret: str
    passphrase: Optional[str] = None

class KeyVault:
    def __init__(self):
        self._store = {}

    def put(self, name: str, keys: ApiKeys):
        self._store[name] = keys

    def get(self, name: str) -> Optional[ApiKeys]:
        return self._store.get(name)

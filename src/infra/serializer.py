
import json
from typing import Any, Dict

SCHEMA_VERSION = "1.0.0"

def to_json(obj: Dict[str, Any]) -> str:
    payload = {"_schema_version": SCHEMA_VERSION, **obj}
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))

def from_json(s: str) -> Dict[str, Any]:
    data = json.loads(s)
    return data

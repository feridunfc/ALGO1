# src/core/validators/schema.py
import pandas as pd
from dataclasses import dataclass
from typing import Dict, Any

DATA_SCHEMA = {
    "columns": ["open", "high", "low", "close", "volume"],
    "index": "DatetimeIndex"
}

@dataclass
class SchemaValidator:
    schema: Dict[str, Any]

    def validate(self, df: pd.DataFrame) -> None:
        missing = [c for c in self.schema["columns"] if c not in df.columns]
        if missing:
            raise ValueError(f"SchemaValidator: missing columns {missing}")
        if not isinstance(df.index, pd.DatetimeIndex):
            raise TypeError("SchemaValidator: index must be DatetimeIndex")
        if not df.index.is_monotonic_increasing:
            raise ValueError("SchemaValidator: index must be monotonic increasing")
        if not df.index.is_unique:
            raise ValueError("SchemaValidator: index must be unique")

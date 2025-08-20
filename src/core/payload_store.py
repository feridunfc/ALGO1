from __future__ import annotations
from pathlib import Path
from typing import Any
import pandas as pd
import pickle
import hashlib
import logging

logger = logging.getLogger("core.payload_store")


class PayloadStore:
    """
    Basit disk tabanlı payload deposu.
    - DataFrame'leri parquet olarak, diğerlerini pickle olarak saklar.
    - digest(): payload bütünlüğü için stabil SHA256 döndürür.
    """
    def __init__(self, storage_path: Path):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

    def save(self, payload: Any, ref_name: str) -> str:
        """Payload'ı kaydet ve dosya adını (relative ref) döndür."""
        safe_name = (
            str(ref_name)
            .replace(":", "_")
            .replace("/", "_")
            .replace("\\", "_")
        )
        if isinstance(payload, pd.DataFrame):
            filename = f"{safe_name}.parquet"
            path = self.storage_path / filename
            payload.to_parquet(path)
        else:
            filename = f"{safe_name}.pkl"
            path = self.storage_path / filename
            with open(path, "wb") as f:
                pickle.dump(payload, f)
        logger.debug("Payload saved: %s", filename)
        return filename

    def load(self, payload_ref: str) -> Any:
        """Ref ile payload'ı yükle."""
        path = self.storage_path / payload_ref
        if not path.exists():
            raise FileNotFoundError(f"Payload {payload_ref} not found")
        if payload_ref.endswith(".parquet"):
            return pd.read_parquet(path)
        else:
            with open(path, "rb") as f:
                return pickle.load(f)

    def digest(self, payload: Any) -> str:
        """
        Stabil bir SHA256 üret. DataFrame için pandas'ın hash mekanizmasını kullan.
        """
        try:
            if isinstance(payload, pd.DataFrame):
                arr = pd.util.hash_pandas_object(payload, index=True).values
                return hashlib.sha256(arr.tobytes()).hexdigest()
            elif isinstance(payload, pd.Series):
                arr = pd.util.hash_pandas_object(payload, index=True).values
                return hashlib.sha256(arr.tobytes()).hexdigest()
            else:
                return hashlib.sha256(pickle.dumps(payload)).hexdigest()
        except Exception:
            # En kötü senaryoda yine pickle üzerinden üretelim (stabil olsun)
            return hashlib.sha256(pickle.dumps(payload)).hexdigest()

    # Geriye dönük uyumluluk: bazı testler/yerler generate_digest adını bekleyebilir
    def generate_digest(self, payload: Any) -> str:  # pragma: no cover
        return self.digest(payload)


import os
from typing import Optional

def get_api_key(name: str) -> Optional[str]:
    # Basit env tabanlı gizli yükleyici (Vault/SM entegrasyonu için kanca)
    return os.getenv(name)

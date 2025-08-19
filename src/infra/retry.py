
from __future__ import annotations
import time

def retry(func, attempts: int = 3, backoff_sec: float = 0.1):
    last = None
    for i in range(attempts):
        try:
            return func()
        except Exception as e:
            last = e
            if i < attempts - 1:
                time.sleep(backoff_sec * (2**i))
    if last:
        raise last

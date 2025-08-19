# src/utils/nlp_utils.py
from typing import Optional

def safe_import_transformers():
    try:
        import transformers  # noqa: F401
        return True
    except Exception:
        return False

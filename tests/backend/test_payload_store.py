
import pandas as pd
import tempfile
import pytest
from pathlib import Path

# Robust imports
try:
    from src.core.payload_store import PayloadStore
except Exception:
    from core.payload_store import PayloadStore

def test_payload_store_roundtrip_dataframe():
    with tempfile.TemporaryDirectory() as d:
        store = PayloadStore(Path(d))
        df = pd.DataFrame({"a":[1,2,3], "b":[10.0, 11.0, 12.0]})
        try:
            ref = store.save(df, "df_roundtrip")
        except (ImportError, ValueError) as e:
            pytest.skip(f"Parquet engine missing or invalid: {e}")
        loaded = store.load(ref)
        pd.testing.assert_frame_equal(df, loaded)

def test_payload_store_digest_len():
    with tempfile.TemporaryDirectory() as d:
        store = PayloadStore(Path(d))
        df = pd.DataFrame({"x":[1,2]})
        try:
            digest = store.digest(df)
        except (ImportError, ValueError) as e:
            pytest.skip(f"Parquet engine missing: {e}")
        assert isinstance(digest, str) and len(digest) == 64

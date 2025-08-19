import pandas as pd
import pytest
from src.core.data_normalizer import DataNormalizer
from src.core.config import NormalizationConfig

def fixed_random_seed(seed=42):
    import contextlib, random, numpy as np
    @contextlib.contextmanager
    def _ctx():
        st = np.random.get_state()
        rnd = random.getstate()
        np.random.seed(seed); random.seed(seed)
        try: yield
        finally:
            np.random.set_state(st); random.setstate(rnd)
    return _ctx()

def load_fixture(name: str) -> pd.DataFrame:
    return pd.read_csv(f"tests/fixtures/{name}", parse_dates=["timestamp"], index_col="timestamp")

def load_expected_output(path: str) -> pd.DataFrame:
    import os
    parq = "tests/fixtures/golden_expected.parquet"
    csvp = "tests/fixtures/golden_expected.csv"
    if os.path.exists(parq):
        return pd.read_parquet(parq)
    return pd.read_csv(csvp, parse_dates=["timestamp"], index_col="timestamp")

def test_golden_series_strict_ok():
    normalizer = DataNormalizer(NormalizationConfig(scaler="zscore"), strict_mode=True)
    test_data = load_fixture("golden_sample.csv")

    assert not test_data.isnull().any().any()

    with fixed_random_seed(42):
        result = normalizer.fit_transform(test_data, symbol="TEST")

    expected = load_expected_output("golden_expected.parquet")
    pd.testing.assert_frame_equal(result, expected, atol=1e-5, rtol=1e-5, check_freq=False)

def test_index_contract():
    normalizer = DataNormalizer(strict_mode=False)
    test_data = load_fixture("golden_sample.csv")
    out = normalizer.fit_transform(test_data)
    assert out.index.is_monotonic_increasing and out.index.is_unique and out.index.tz is not None
    assert list(out.columns) == ["open","high","low","close","volume"]

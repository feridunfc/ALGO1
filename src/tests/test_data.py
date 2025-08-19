import pandas as pd
from ..data.validation import validate_ohlc, normalize_ohlc_columns, ensure_timezone

def test_data_validation_basic():
    idx = pd.date_range("2022-01-01", periods=10, freq="B")
    df = pd.DataFrame({
        "Open": 100.0, "High": 101.0, "Low": 99.0, "Close": 100.5, "Volume": 1000
    }, index=idx)
    df = normalize_ohlc_columns(df)
    df = ensure_timezone(df, "UTC")
    validate_ohlc(df)

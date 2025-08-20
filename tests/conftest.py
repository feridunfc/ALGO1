# conftest.py (root seviyesinde)
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timezone
from pathlib import Path

from src.core.backtest_engine import BacktestEngine
from src.backend.eventbus import EventBus
from src.backend.risk_engine import RiskEngine


@pytest.fixture(scope="session")
def test_data_dir() -> Path:
    """Test verilerinin bulunduğu klasörü döndürür."""
    return Path(__file__).parent / "data"


@pytest.fixture(scope="function")
def dummy_dataframe():
    """NaN içermeyen basit bir DataFrame örneği."""
    return pd.DataFrame({
        "timestamp": pd.date_range(datetime.now(timezone.utc), periods=5, freq="D"),
        "price": np.linspace(100, 105, 5),
        "volume": [10, 20, 30, 40, 50],
    })


@pytest.fixture(scope="function")
def event_bus():
    """Her test için izole EventBus sağlar."""
    return EventBus()


@pytest.fixture(scope="function")
def risk_engine():
    """Varsayılan parametrelerle risk motoru döndürür."""
    return RiskEngine(max_position_size=1000, max_notional=1e6)


@pytest.fixture(scope="function")
def backtest_engine(event_bus, risk_engine):
    """Basit bir backtest engine fixture."""
    return BacktestEngine(event_bus=event_bus, risk_engine=risk_engine)


def pytest_configure(config):
    """Custom mark'ları register et (ör. ui harici)."""
    config.addinivalue_line("markers", "backend: backend testleri için")
    config.addinivalue_line("markers", "integration: entegrasyon testleri için")

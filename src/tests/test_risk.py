
import numpy as np
import pandas as pd
from ..risk.position_sizing import VolatilityPositionSizer
from ..risk.manager import AdvancedRiskManager

def test_volatility_targeting():
    closes = pd.Series(100.0 + np.random.randn(1000).cumsum())
    sizer = VolatilityPositionSizer(target_annual_vol=0.30, lookback_days=30, max_position_weight_pct=0.10)
    size_value = sizer.calculate_size_value(closes, 100000.0)
    assert 0 <= size_value <= 100000.0 * 0.10

def test_advanced_risk_manager():
    rm = AdvancedRiskManager(target_vol=0.20, max_position_weight_pct=0.10)
    pos = rm.calculate_position(symbol_vol_daily=0.02, portfolio_value=100000.0)
    assert 0 <= pos <= 100000.0 * 0.10


from __future__ import annotations
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path

from src.core.config import Config
from src.core.strategy_factory import StrategyFactory
from src.core.market_regime_detector import MarketRegimeDetector
from src.core.enhanced_risk_engine import EnhancedRiskEngine

def make_sine_price(n=300, start=100.0, noise=0.01):
    x = np.arange(n)
    price = start * (1 + 0.1*np.sin(2*np.pi*x/100.0))
    shocks = np.random.normal(0, noise, size=n).cumsum()
    return price * (1 + shocks)

def build_asset_df(n=300):
    idx = pd.date_range(end=datetime.utcnow(), periods=n, freq="D")
    close = pd.Series(make_sine_price(n), index=idx)
    high = close * (1 + 0.005)
    low = close * (1 - 0.005)
    openp = close.shift(1).fillna(close.iloc[0])
    vol = pd.Series(np.random.lognormal(mean=12, sigma=0.4, size=n), index=idx)
    df = pd.DataFrame({"open": openp, "high": high, "low": low, "close": close, "volume": vol})
    return df

def main():
    cfg = Config()
    factory = StrategyFactory(cfg)
    regime = MarketRegimeDetector()

    ere = EnhancedRiskEngine(cfg, factory, regime)

    features = build_asset_df(320)
    asset = {
        "ticker": "AAPL",
        "features": features,
        "technicals": features,  # for demo same
        "fundamentals": {"pe_ratio": 24.5, "debt_to_equity": 1.2},
        "liquidity": {"avg_dollar_volume_30d": 8_000_000},
    }

    decision = ere.generate_decision(asset)
    print("Decision:")
    for k, v in decision.items():
        print(f"  {k}: {v}")

if __name__ == "__main__":
    main()

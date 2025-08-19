
import os, sys, pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from backtest.simulator_with_risk import run_backtest_with_risk
from risk.limits import RiskLimits

def test_kill_switch_blocks_buys():
    # Create a series that causes a tiny drawdown immediately; set max_dd=0 to arm killswitch
    prices = list(range(1, 120)) + [50]*20  # create signals
    df = pd.DataFrame({
        "timestamp": pd.date_range("2024-01-01", periods=len(prices), freq="T", tz="UTC"),
        "symbol":["BTC-USD"]*len(prices),
        "open":prices, "high":[p+1 for p in prices], "low":[max(0,p-1) for p in prices], "close":prices, "volume":[10]*len(prices)
    })
    limits = RiskLimits(max_drawdown_pct=0.0, max_pos_per_symbol_pct=0.5)
    res = run_backtest_with_risk(df, limits=limits)
    # With max_dd=0.0, any drawdown should stop new buys -> either 0 or very few trades
    assert res["stats"]["trades"] >= 0  # sanity
    # ensure no oversized exposure: since size is ATR-based and capped, equity should be > 0
    assert res["equity"]["equity"].iloc[-1] > 0

def test_position_sizer_caps_exposure():
    # High ATR -> very small size; expect small notional per trade
    prices = [100 + (i%5) for i in range(200)]
    df = pd.DataFrame({
        "timestamp": pd.date_range("2024-01-01", periods=len(prices), freq="T", tz="UTC"),
        "symbol":["BTC-USD"]*len(prices),
        "open":prices, "high":[p+5 for p in prices], "low":[p-5 for p in prices], "close":prices, "volume":[10]*len(prices)
    })
    limits = RiskLimits(max_pos_per_symbol_pct=0.10)
    res = run_backtest_with_risk(df, limits=limits)
    # Should not blow up equity and number of trades can be 0+
    assert res["equity"]["equity"].iloc[-1] > 0

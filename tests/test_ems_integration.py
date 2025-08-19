
import os, sys, pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from infra.event_bus import EventBus
from data_layer.replayer import DataReplayer
from backtest.broker_virtual import VirtualBroker
from execution.ems import EMS
from execution.gateway_sim import ExchangeGatewaySim
from schemas.events import Event

def test_ems_twap_and_broker():
    # build synthetic data: 10 bars
    prices = [100 + i for i in range(10)]
    df = pd.DataFrame({
        "timestamp": pd.date_range("2024-01-01", periods=len(prices), freq="T", tz="UTC"),
        "symbol":["BTC-USD"]*len(prices),
        "open":prices, "high":[p+1 for p in prices], "low":[max(0,p-1) for p in prices], "close":prices, "volume":[100]*len(prices)
    })
    bus = EventBus()
    broker = VirtualBroker(start_cash=10_000.0, fee_bps=0.0, slippage_bps=0.0, exec_mode="next_open", bus=bus)
    broker.subscribe(bus)
    ems = EMS(bus, default_algo="TWAP", bars_per_parent=5)
    gw = ExchangeGatewaySim(bus)

    # Emit a risk-approved BUY signal for 5 qty
    sig = {"symbol":"BTC-USD", "side":"BUY", "size_hint":5.0}
    bus.publish("SIGNAL_APPROVED", Event.create("SIGNAL","test",{ "signal": sig}).asdict())

    # Replay bars -> EMS releases 5 slices across 5 bars; broker fills
    DataReplayer(df, source="unit").run_sync(bus)

    trades = broker.trades_frame()
    # Expect ~5 buys total qty ~5
    assert len(trades) >= 5
    assert abs(trades["qty"].sum() - 5.0) < 1e-9

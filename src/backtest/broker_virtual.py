
from __future__ import annotations
from typing import Dict, Any
import pandas as pd

class VirtualBroker:
    def __init__(self, start_cash: float, fee_bps: float, slippage_bps: float, exec_mode: str, bus):
        self.start_cash = start_cash; self.bus = bus
    def subscribe(self, bus): pass
    def equity_curve(self): return pd.DataFrame({"t":[], "equity":[]})
    def trades_frame(self): return pd.DataFrame({"symbol":[], "side":[], "qty":[], "px":[], "fee":[], "t":[], "pnl":[]})
    def snapshot(self): return {}

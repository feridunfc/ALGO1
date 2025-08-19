
from __future__ import annotations
from typing import Dict, Any, List
from dataclasses import dataclass
import pandas as pd
from schemas.events import Event

@dataclass
class Position:
    symbol: str
    qty: float = 0.0
    avg_px: float = 0.0

class PortfolioLedger:
    def __init__(self, bus, start_cash: float = 100_000.0):
        self.bus = bus
        self.cash = float(start_cash)
        self.positions: Dict[str, Position] = {}
        self.last_px: Dict[str, float] = {}
        self.equity_hist: List[Dict[str, Any]] = []
        self.trades: List[Dict[str, Any]] = []
        bus.subscribe("BROKER_TRADE", self.on_trade)
        bus.subscribe("MARKET_DATA", self.on_market)

    def on_trade(self, ev: Dict[str, Any]):
        tr = ev.get("payload", {}).get("trade")
        if not tr:
            return
        sym = tr["symbol"]; side = tr["side"]; qty = float(tr["qty"]); px = float(tr["px"]); fee = float(tr.get("fee",0.0))
        if side == "BUY":
            self.cash -= px*qty + fee
            pos = self.positions.get(sym, Position(symbol=sym))
            new_qty = pos.qty + qty
            pos.avg_px = (pos.qty*pos.avg_px + qty*px)/max(new_qty,1e-9)
            pos.qty = new_qty
            self.positions[sym] = pos
        else:
            pos = self.positions.get(sym, Position(symbol=sym))
            exec_qty = min(pos.qty, qty)
            self.cash += px*exec_qty - fee
            pos.qty -= exec_qty
            if pos.qty <= 1e-12:
                pos.qty = 0.0
            self.positions[sym] = pos
        self.trades.append(tr)

    def on_market(self, ev: Dict[str, Any]):
        payload = ev.get("payload", {})
        sym = payload.get("symbol")
        bar = payload.get("bar")
        if not sym or not bar:
            return
        self.last_px[sym] = float(bar["c"])
        eq = self.cash
        for s, pos in self.positions.items():
            px = self.last_px.get(s, float(bar["c"] if s == sym else 0.0))
            eq += pos.qty * px
        self.equity_hist.append({"t": bar["t"], "equity": eq})
        self.bus.publish("EQUITY", Event.create("RISK","ledger", {"t": bar["t"], "equity": eq}).asdict())

    def equity_curve(self):
        import pandas as pd
        if not self.equity_hist:
            return pd.DataFrame(columns=["t","equity"])
        df = pd.DataFrame(self.equity_hist)
        df["t"] = pd.to_datetime(df["t"], utc=True)
        return df

    def trades_frame(self):
        import pandas as pd
        if not self.trades:
            return pd.DataFrame(columns=["symbol","side","qty","px","fee","t","pnl"])
        df = pd.DataFrame(self.trades)
        df["t"] = pd.to_datetime(df["t"], utc=True)
        if "pnl" not in df.columns:
            df["pnl"] = 0.0
        return df

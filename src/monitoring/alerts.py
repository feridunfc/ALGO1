
from __future__ import annotations
from typing import Dict, Any, List
import pandas as pd
from schemas.events import Event

class AlertManager:
    def __init__(self, bus, dd_threshold: float = 0.1, risk_reject_streak: int = 5):
        self.bus = bus; self.dd_threshold = dd_threshold
        self.eq_hist: List[Dict[str, Any]] = []
        bus.subscribe("EQUITY", self.on_equity)

    def on_equity(self, ev: Dict[str, Any]):
        payload = ev.get("payload", {})
        t = payload.get("t"); eq = float(payload.get("equity", 0.0))
        self.eq_hist.append({"t": t, "equity": eq})
        df = pd.DataFrame(self.eq_hist)
        dd = (df["equity"] / df["equity"].cummax() - 1.0).iloc[-1]
        if dd <= -abs(self.dd_threshold):
            alert = {"type":"DRAWDOWN", "severity":"CRITICAL", "drawdown": float(dd), "t": t}
            self.bus.publish("ALERT", Event.create("ALERT","alerts", {"alert": alert}).asdict())

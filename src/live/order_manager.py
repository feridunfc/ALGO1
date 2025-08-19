from __future__ import annotations
import queue, threading, time
from dataclasses import dataclass, field
from typing import Dict, List
import numpy as np

@dataclass(order=True)
class PrioritizedOrder:
    priority: int
    submit_ts: float
    order: dict = field(compare=False)

class OrderManager:
    """
    Async OMS: PriorityQueue + latency jitter + ADV tabanlı VWAP slippage.
    """
    def __init__(self, latency_mean: float = 0.1, latency_std: float = 0.02):
        self.q: queue.PriorityQueue[PrioritizedOrder] = queue.PriorityQueue()
        self.fills: Dict[str, List[dict]] = {}
        self.latency_mean = latency_mean
        self.latency_std = latency_std
        self._running = False

    def start(self):
        if self._running: return
        self._running = True
        threading.Thread(target=self._loop, daemon=True).start()

    def stop(self):
        self._running = False

    def submit(self, order: dict):
        prio = 0 if order.get("type","LIMIT") == "LIMIT" else 1
        self.q.put(PrioritizedOrder(prio, time.time(), order))

    def _loop(self):
        while self._running:
            try:
                po: PrioritizedOrder = self.q.get(timeout=0.1)
            except Exception:
                continue
            delay = max(0.0, np.random.normal(self.latency_mean, self.latency_std))
            time.sleep(delay)
            qty = abs(float(po.order.get("qty", 0.0)))
            adv = max(1.0, float(po.order.get("adv", 1e6)))
            impact = (qty/adv) * 0.1
            price = float(po.order["price"]) * (1 + impact if po.order.get("side","BUY")=="BUY" else 1 - impact)
            sym = po.order["symbol"]
            rec = {"timestamp": time.time(), "price": price, "qty": qty, "side": po.order.get("side","BUY")}
            self.fills.setdefault(sym, []).append(rec)

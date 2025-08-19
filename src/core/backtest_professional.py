from __future__ import annotations
import pandas as pd
from dataclasses import dataclass
from datetime import timedelta
from typing import Callable, Dict, List
from .slippage.volume_weighted import apply_vwap_slippage

@dataclass
class Order:
    ts: pd.Timestamp
    symbol: str
    side: int        # +1 buy, -1 sell
    qty: float
    ref_price: float

class ProfessionalBacktestEngine:
    """
    Yeni dosya/sınıf; mevcut engine’e dokunmaz.
    • 1-bar delay
    • Commission (bps) + VWAP slippage
    • Trade log + cash/pozisyon muhasebesi
    • Multi-asset equity
    """
    def __init__(
        self,
        commission_bps: float = 10.0,
        min_slippage_bps: float = 5.0,
        impact: float = 0.1,
        base_cash: float = 100_000.0,
        latency: timedelta = timedelta(milliseconds=50),
    ):
        self.commission_bps = commission_bps
        self.min_slippage_bps = min_slippage_bps
        self.impact = impact
        self.latency = latency
        self.cash = base_cash
        self.positions: Dict[str, float] = {}
        self.trade_log: List[dict] = []

    def run(
        self,
        price_panel: Dict[str, pd.DataFrame],
        adv_map: Dict[str, float],
        signal_fn: Callable[[pd.Timestamp, Dict[str, pd.Series]], Dict[str, float]],
    ) -> Dict[str, pd.Series]:
        # ortak index
        common_index = None
        for df in price_panel.values():
            common_index = df.index if common_index is None else common_index.intersection(df.index)
        common_index = common_index.sort_values()

        equity_curve = []
        pending_orders: List[Order] = []
        last_row_map = {}

        for i, ts in enumerate(common_index):
            row_map = {s: price_panel[s].loc[ts] for s in price_panel}

            # pending fill
            still = []
            for od in pending_orders:
                if ts - od.ts >= self.latency:
                    ref = row_map[od.symbol].get("ask" if od.side > 0 else "bid", row_map[od.symbol]["close"])
                    adv = adv_map.get(od.symbol, 1_000_000)
                    fill, _ = apply_vwap_slippage(ref, "BUY" if od.side > 0 else "SELL", od.qty, adv,
                                                  impact=self.impact, min_bps=self.min_slippage_bps)
                    commission_cash = (self.commission_bps / 10_000.0) * fill * od.qty
                    trade_cash = fill * od.qty * od.side
                    self.cash -= trade_cash + commission_cash
                    self.positions[od.symbol] = self.positions.get(od.symbol, 0.0) + (od.qty * od.side)
                    self.trade_log.append({
                        "timestamp": ts, "symbol": od.symbol, "side": od.side, "qty": od.qty,
                        "fill_price": fill, "ref_price": od.ref_price,
                        "commission_cash": commission_cash, "cash_after": self.cash,
                    })
                else:
                    still.append(od)
            pending_orders = still

            # sinyal üret (T+1 icra)
            if i > 0:
                targets = signal_fn(ts, last_row_map)  # {-1..+1} weight
                equity = self._calc_equity(row_map)
                for sym, tgt_w in targets.items():
                    price = row_map[sym]["close"]
                    target_value = equity * float(tgt_w)
                    cur_qty = self.positions.get(sym, 0.0)
                    cur_value = cur_qty * price
                    delta_value = target_value - cur_value
                    if abs(delta_value) <= 1e-9:
                        continue
                    qty = max(0.0, abs(delta_value) / price)
                    side = 1 if delta_value > 0 else -1
                    if qty > 0:
                        pending_orders.append(Order(ts=ts, symbol=sym, side=side, qty=qty, ref_price=price))

            equity_curve.append(self._calc_equity(row_map))
            last_row_map = row_map

        equity_series = pd.Series(equity_curve, index=common_index, name="equity")
        trades_df = pd.DataFrame(self.trade_log)
        return {"equity": equity_series, "trades": trades_df,
                "positions_final": self.positions.copy(), "cash_final": self.cash}

    def _calc_equity(self, row_map: Dict[str, pd.Series]) -> float:
        pos_val = sum(self.positions.get(sym, 0.0) * row_map[sym]["close"] for sym in row_map)
        return self.cash + pos_val

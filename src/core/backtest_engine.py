
# src/core/backtest_engine.py
from __future__ import annotations

import math
import uuid
import logging
from dataclasses import dataclass
from enum import Enum, auto
from typing import Dict, List, Optional, Any
import pandas as pd
import numpy as np

logger = logging.getLogger("BacktestEngine")
logger.setLevel(logging.INFO)


class OrderType(Enum):
    MARKET = auto()
    LIMIT = auto()
    STOP = auto()


class OrderDirection(Enum):
    LONG = 1
    SHORT = -1
    FLAT = 0


@dataclass
class Trade:
    """Full-fidelity trade record for academic-grade analysis."""
    trade_id: str
    symbol: str
    entry_time: pd.Timestamp
    exit_time: Optional[pd.Timestamp]
    entry_price: float
    exit_price: Optional[float]
    quantity: float
    direction: OrderDirection
    order_type: OrderType
    commission: float
    slippage: float
    pnl: Optional[float]
    pnl_pct: Optional[float]
    holding_period: Optional[float]  # in days (or bars if intraday)
    volatility: float  # realized (bar) vol at entry
    sharpe_ratio: Optional[float] = None
    max_drawdown: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


class CommissionModel:
    """Abstract-ish commission model base (duck-typed)."""
    def calculate(self, order_notional: float) -> float:
        raise NotImplementedError


class FixedCommissionModel(CommissionModel):
    def __init__(self, fixed_commission: float):
        self.fixed = float(fixed_commission)

    def calculate(self, order_notional: float) -> float:
        return float(self.fixed)


class PercentageCommissionModel(CommissionModel):
    def __init__(self, rate: float, min_commission: float = 0.0):
        self.rate = float(rate)
        self.min = float(min_commission)

    def calculate(self, order_notional: float) -> float:
        return max(self.min, float(order_notional) * self.rate)


class SlippageModel:
    def calculate(self, symbol: str, order_notional: float, current_volatility: float) -> float:
        """Return slippage as a fraction of price (e.g., 0.0002 == 2bps)."""
        raise NotImplementedError


class VolatilityProportionalSlippage(SlippageModel):
    def __init__(self, base_rate: float = 0.0005):
        self.base = float(base_rate)

    def calculate(self, symbol: str, order_notional: float, current_volatility: float) -> float:
        # modest non-linear scaling with size and proportional to bar volatility
        size_factor = np.log1p(max(order_notional, 0.0) / 1e6)  # ~0 for small orders
        return float(self.base) * float(current_volatility) * float(max(size_factor, 0.0))


class BacktestEngine:
    """
    Industrial-grade backtest engine:
     - 1-bar execution delay
     - Commission/slippage plug-ins
     - Multi-asset portfolio accounting
     - Detailed trade log
     - Robust metrics (Sharpe, MaxDD, win rate, turnover, etc.)
    """

    def __init__(
        self,
        price_data: Dict[str, pd.DataFrame],
        initial_capital: float = 1_000_000.0,
        commission_model: Optional[CommissionModel] = None,
        slippage_model: Optional[SlippageModel] = None,
        risk_free_rate: float = 0.0,
    ) -> None:
        self._validate_price_data(price_data)
        self.price_data = {sym: df.sort_index() for sym, df in price_data.items()}
        self.initial_capital = float(initial_capital)
        self.commission_model = commission_model or PercentageCommissionModel(0.0005, min_commission=0.0)
        self.slippage_model = slippage_model or VolatilityProportionalSlippage()
        self.risk_free_rate = float(risk_free_rate)

        # Derived
        self._common_dates = self._compute_common_dates()

        # State
        self.current_date: Optional[pd.Timestamp] = None
        self.portfolio_cash: float = float(initial_capital)
        self.positions: Dict[str, float] = {sym: 0.0 for sym in self.price_data.keys()}  # qty (+ long, - short)
        self.avg_price: Dict[str, float] = {sym: 0.0 for sym in self.price_data.keys()}  # avg entry for position
        self.trade_log: List[Trade] = []
        self.order_book: List[Dict[str, Any]] = []

        # History
        self.portfolio_history = pd.Series(dtype=float)
        self.returns = pd.Series(dtype=float)

    # ---------------------- Lifecycle ----------------------
    def run(self, start_date: pd.Timestamp, end_date: pd.Timestamp) -> Dict[str, Any]:
        start_date = pd.Timestamp(start_date)
        end_date = pd.Timestamp(end_date)
        if start_date > end_date:
            raise ValueError("start_date cannot be after end_date")

        window_dates = self._window_dates(start_date, end_date)
        if len(window_dates) < 2:
            raise ValueError("Not enough common dates in the given window.")

        # schedule pre-submitted orders lacking dates to T+1 of start
        for order in self.order_book:
            if order.get("submission_date") is None:
                order["submission_date"] = window_dates[0]
            if order.get("execution_date") is None:
                order["execution_date"] = self._next_trading_day_from(order["submission_date"], window_dates)

        last_value = None
        for dt in window_dates:
            self.current_date = dt
            # process orders scheduled for today
            self._process_orders_for_today()
            # MTM valuation
            value = self._mark_to_market()
            self.portfolio_history.loc[dt] = value
            if last_value is not None and last_value > 0:
                self.returns.loc[dt] = (value / last_value) - 1.0
            last_value = value

        report = self._generate_report()
        return report

    # ---------------------- Orders & Execution ----------------------
    def submit_order(
        self,
        symbol: str,
        direction: OrderDirection,
        quantity: float,
        order_type: OrderType = OrderType.MARKET,
        limit_price: Optional[float] = None,
        strategy: Optional[str] = None,
        submission_date: Optional[pd.Timestamp] = None,
    ) -> str:
        """Queue a new order. If called before run(), we infer dates at run()."""
        if symbol not in self.price_data:
            raise ValueError(f"Unknown symbol: {symbol}")
        if quantity <= 0:
            raise ValueError("quantity must be positive")
        if order_type == OrderType.LIMIT and limit_price is None:
            raise ValueError("limit_price required for LIMIT orders")

        order_id = f"ORD_{len(self.order_book)+1}_{symbol}"
        order = {
            "order_id": order_id,
            "symbol": symbol,
            "direction": direction,
            "quantity": float(quantity),
            "order_type": order_type,
            "limit_price": float(limit_price) if limit_price is not None else None,
            "strategy": strategy or "unknown",
            "submission_date": pd.Timestamp(submission_date) if submission_date is not None else None,
            "execution_date": None,  # to be set at run() or next day if current_date provided
        }

        # if we are mid-run and have a current date, schedule to next trading day
        if self.current_date is not None:
            order["submission_date"] = self.current_date
            order["execution_date"] = self._next_trading_day_from(self.current_date, self._common_dates)

        self.order_book.append(order)
        logger.debug(f"Order submitted: {order}")
        return order_id

    def _process_orders_for_today(self) -> None:
        """Execute all orders whose execution_date is today."""
        to_remove = []
        for order in self.order_book:
            if order["execution_date"] is None:
                # If not scheduled (shouldn't happen mid-run), skip
                continue
            if order["execution_date"] != self.current_date:
                continue
            try:
                trade = self._execute_order(order)
                if trade is not None:
                    self.trade_log.append(trade)
                to_remove.append(order)
            except Exception as e:
                logger.error(f"Execution failed for {order['order_id']}: {e}")
                to_remove.append(order)

        # Remove processed
        self.order_book = [o for o in self.order_book if o not in to_remove]

    def _execute_order(self, order: Dict[str, Any]) -> Optional[Trade]:
        sym = order["symbol"]
        # fetch today's bar for execution (1-bar delay already applied by scheduling)
        try:
            bar = self.price_data[sym].loc[self.current_date]
        except KeyError:
            logger.warning(f"No bar for {sym} on {self.current_date}")
            return None

        # base execution price
        if order["order_type"] == OrderType.MARKET:
            exec_price = float(bar["open"])
        elif order["order_type"] == OrderType.LIMIT:
            # simplistic limit: filled at best of limit/open depending on side
            if order["direction"] == OrderDirection.LONG:
                exec_price = float(min(order["limit_price"], bar["open"]))
            else:
                exec_price = float(max(order["limit_price"], bar["open"]))
        else:
            raise ValueError("STOP orders not implemented in this hotfix")

        # slippage as fraction
        bar_vol = float((bar["high"] - bar["low"]) / max(bar["open"], 1e-12))
        notional = float(order["quantity"]) * exec_price
        slip_frac = float(self.slippage_model.calculate(sym, notional, bar_vol))
        # apply slippage against us
        if order["direction"] == OrderDirection.LONG:
            exec_price *= (1.0 + slip_frac)
        else:
            exec_price *= (1.0 - slip_frac)

        # commission in dollars
        commission = float(self.commission_model.calculate(notional))

        trade = Trade(
            trade_id=f"TRD_{len(self.trade_log)+1}_{sym}",
            symbol=sym,
            entry_time=self.current_date,
            exit_time=None,
            entry_price=float(exec_price),
            exit_price=None,
            quantity=float(order["quantity"]),
            direction=order["direction"],
            order_type=order["order_type"],
            commission=commission,
            slippage=slip_frac * notional,
            pnl=None,
            pnl_pct=None,
            holding_period=None,
            volatility=bar_vol,
            metadata={
                "order_id": order["order_id"],
                "strategy": order.get("strategy", "unknown"),
                "submission_date": str(order.get("submission_date", "")),
            },
        )

        self._apply_trade_to_positions(trade)
        return trade

    # ---------------------- Portfolio Accounting ----------------------
    def _apply_trade_to_positions(self, trade: Trade) -> None:
        sym = trade.symbol
        qty = trade.quantity * (1 if trade.direction == OrderDirection.LONG else -1)
        total_cost = trade.entry_price * trade.quantity + trade.commission
        # cash moves: buying reduces cash, selling increases
        self.portfolio_cash -= total_cost if qty > 0 else - (trade.entry_price * trade.quantity - trade.commission)

        prev_qty = self.positions.get(sym, 0.0)
        prev_avg = self.avg_price.get(sym, 0.0)

        new_qty = prev_qty + qty

        if prev_qty == 0 or (prev_qty > 0 and qty > 0) or (prev_qty < 0 and qty < 0):
            # adding to existing same-direction position or opening
            if new_qty != 0:
                # weighted average price
                self.avg_price[sym] = (prev_avg * abs(prev_qty) + trade.entry_price * abs(qty)) / (abs(prev_qty) + abs(qty))
        else:
            # reducing / closing or flipping direction
            if np.sign(prev_qty) != np.sign(new_qty) and new_qty != 0:
                # flipped: set avg to trade price for remaining side
                self.avg_price[sym] = trade.entry_price
            elif new_qty == 0:
                self.avg_price[sym] = 0.0

        self.positions[sym] = new_qty

    def _mark_to_market(self) -> float:
        """Compute current portfolio value (cash + positions @ close)."""
        total = float(self.portfolio_cash)
        for sym, qty in self.positions.items():
            if qty == 0:
                continue
            try:
                px = float(self.price_data[sym].loc[self.current_date]["close"])
            except KeyError:
                continue
            total += qty * px
        return total

    # ---------------------- Reports & Metrics ----------------------
    def _generate_report(self) -> Dict[str, Any]:
        perf = self._calculate_performance_metrics()
        trades_df = self._trades_dataframe()
        return {
            "performance": perf,
            "trades": trades_df,
            "portfolio_history": self.portfolio_history.copy(),
            "returns": self.returns.copy(),
        }

    def _trades_dataframe(self) -> pd.DataFrame:
        if not self.trade_log:
            return pd.DataFrame(columns=[f.name for f in Trade.__dataclass_fields__.values()])
        rows = []
        for t in self.trade_log:
            rows.append({
                "trade_id": t.trade_id,
                "symbol": t.symbol,
                "entry_time": t.entry_time,
                "exit_time": t.exit_time,
                "entry_price": t.entry_price,
                "exit_price": t.exit_price,
                "quantity": t.quantity,
                "direction": t.direction.name,
                "order_type": t.order_type.name,
                "commission": t.commission,
                "slippage": t.slippage,
                "pnl": t.pnl,
                "pnl_pct": t.pnl_pct,
                "holding_period": t.holding_period,
                "volatility": t.volatility,
                "sharpe_ratio": t.sharpe_ratio,
                "max_drawdown": t.max_drawdown,
                "metadata": t.metadata or {},
            })
        return pd.DataFrame(rows)

    def _calculate_performance_metrics(self) -> Dict[str, float]:
        out: Dict[str, float] = {}
        rets = self.returns.dropna()
        if len(rets) >= 2 and float(rets.std()) != 0.0:
            rf_daily = self.risk_free_rate / 252.0
            excess = rets - rf_daily
            sharpe = np.sqrt(252.0) * float(excess.mean()) / float(excess.std())
            out["sharpe_ratio"] = sharpe
        else:
            out["sharpe_ratio"] = float("nan")

        # Max Drawdown on equity curve
        eq = self.portfolio_history.dropna()
        if len(eq) >= 2:
            cummax = eq.cummax()
            dd = (eq - cummax) / cummax
            out["max_drawdown"] = float(dd.min())
            out["calmar"] = (eq.iloc[-1] / eq.iloc[0] - 1.0) / abs(out["max_drawdown"]) if out["max_drawdown"] != 0 else float("nan")
        else:
            out["max_drawdown"] = float("nan")
            out["calmar"] = float("nan")

        # Turnover (sum abs(position change in $) / average equity)
        dollar_turnover = 0.0
        last_positions_value = None
        for dt in self.portfolio_history.index:
            pv = 0.0
            for sym, qty in self.positions.items():
                try:
                    px = float(self.price_data[sym].loc[dt]["close"])
                    pv += abs(qty) * px
                except KeyError:
                    continue
            if last_positions_value is not None:
                dollar_turnover += abs(pv - last_positions_value)
            last_positions_value = pv
        avg_equity = float(self.portfolio_history.mean()) if len(self.portfolio_history) else 0.0
        out["turnover"] = dollar_turnover / avg_equity if avg_equity > 0 else float("nan")

        out["total_return"] = (eq.iloc[-1] / eq.iloc[0] - 1.0) if len(eq) >= 2 else float("nan")
        out["num_trades"] = float(len(self.trade_log))

        # Win rate (requires exits; for this hotfix, we compute MTM wins at end vs entry price)
        if self.trade_log:
            wins = 0
            for t in self.trade_log:
                # MTM against close at final date
                last_dt = self.portfolio_history.index[-1]
                try:
                    last_px = float(self.price_data[t.symbol].loc[last_dt]["close"])
                except Exception:
                    last_px = t.entry_price
                pnl = (last_px - t.entry_price) * (t.quantity if t.direction == OrderDirection.LONG else -t.quantity) - t.commission
                if pnl > 0:
                    wins += 1
            out["win_rate"] = wins / len(self.trade_log)
        else:
            out["win_rate"] = float("nan")

        return out

    # ---------------------- Helpers ----------------------
    def _validate_price_data(self, data: Dict[str, pd.DataFrame]) -> None:
        if not data or not isinstance(data, dict):
            raise ValueError("price_data must be a non-empty dict of symbol->DataFrame")
        for sym, df in data.items():
            if not isinstance(df, pd.DataFrame):
                raise TypeError(f"{sym}: expected DataFrame")
            if not isinstance(df.index, pd.DatetimeIndex):
                raise TypeError(f"{sym}: index must be DatetimeIndex")
            required = {"open", "high", "low", "close", "volume"}
            missing = required - set(df.columns)
            if missing:
                raise ValueError(f"{sym}: missing OHLCV columns: {missing}")

    def _compute_common_dates(self) -> pd.DatetimeIndex:
        common = None
        for df in self.price_data.values():
            common = df.index if common is None else common.intersection(df.index)
        if common is None:
            raise ValueError("No dates found")
        return common

    def _window_dates(self, start: pd.Timestamp, end: pd.Timestamp) -> pd.DatetimeIndex:
        mask = (self._common_dates >= start) & (self._common_dates <= end)
        return self._common_dates[mask]

    def _next_trading_day_from(self, current: pd.Timestamp, dates: pd.DatetimeIndex) -> Optional[pd.Timestamp]:
        try:
            idx = dates.get_loc(current)
        except KeyError:
            # choose next greater
            pos = dates.searchsorted(current, side="left")
            idx = int(pos)
        nxt = idx + 1
        if nxt < len(dates):
            return dates[nxt]
        return None

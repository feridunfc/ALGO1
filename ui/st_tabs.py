# ui/st_tabs.py
from __future__ import annotations

import datetime as _dt
from typing import Any, Dict, List

import pandas as pd
import streamlit as st

# --- project imports (mutlak) ---
from config.config import load_config
from pipeline.orchestrator import run_pipeline
from core.strategies.registry import list_strategies
from core.models.registry import list_models


APP_TITLE = "Autonom Trading Platform — 2.9.13 Hotfix"


# -------------- Key helpers & tiny utils --------------
def _k(ns: str, name: str) -> str:
    """Namespaced Streamlit widget key generator to avoid duplicate IDs."""
    return f"{ns}:{name}"


def _to_date(x: Any) -> _dt.date:
    """Coerce incoming date-like to datetime.date for st.date_input."""
    if x is None:
        return _dt.date.today()
    if isinstance(x, _dt.date) and not isinstance(x, _dt.datetime):
        return x
    if isinstance(x, _dt.datetime):
        return x.date()
    try:
        return pd.to_datetime(x).date()
    except Exception:
        return _dt.date.today()


def _to_float(x: Any, default: float = 0.0) -> float:
    try:
        return float(x)
    except Exception:
        return float(default)


def _to_int(x: Any, default: int = 0) -> int:
    try:
        return int(x)
    except Exception:
        return int(default)


# -------------- Config compatibility shim --------------
def _ensure_cfg_compat(cfg):
    """
    Backward/forward compatible field mapping.
    - Ensures fees.commission_bps / fees.slippage_bps exist (derive from *_pct if needed)
    - Stabilizes bt.vol_target (accept *pct naming)
    """
    # Fees
    fees = getattr(cfg, "fees", None)
    if fees is not None:
        # derive values without mutating (for frozen dataclasses we avoid setattr)
        comm_bps = None
        slip_bps = None
        if hasattr(fees, "commission_bps"):
            comm_bps = _to_int(getattr(fees, "commission_bps", 0), 0)
        elif hasattr(fees, "commission_pct"):
            try:
                comm_bps = int(round(float(getattr(fees, "commission_pct")) * 10000))
            except Exception:
                comm_bps = 0
        elif hasattr(fees, "commission"):
            try:
                comm_bps = int(round(float(getattr(fees, "commission")) * 10000))
            except Exception:
                comm_bps = 0
        else:
            comm_bps = 0

        if hasattr(fees, "slippage_bps"):
            slip_bps = _to_int(getattr(fees, "slippage_bps", 0), 0)
        elif hasattr(fees, "slippage_pct"):
            try:
                slip_bps = int(round(float(getattr(fees, "slippage_pct")) * 10000))
            except Exception:
                slip_bps = 0
        else:
            slip_bps = 0

        # store as shadow attributes if needed
        try:
            if not hasattr(fees, "commission_bps"):
                setattr(fees, "commission_bps", comm_bps)
            if not hasattr(fees, "slippage_bps"):
                setattr(fees, "slippage_bps", slip_bps)
        except Exception:
            # create a shadow map on cfg for UI overrides
            try:
                if not hasattr(cfg, "_ui_overrides"):
                    setattr(cfg, "_ui_overrides", {})
                cfg._ui_overrides["commission_bps"] = comm_bps
                cfg._ui_overrides["slippage_bps"] = slip_bps
            except Exception:
                pass

    # Backtest
    bt = getattr(cfg, "bt", None)
    if bt is not None:
        try:
            if not hasattr(bt, "vol_target") and hasattr(bt, "vol_target_pct"):
                setattr(bt, "vol_target", _to_float(getattr(bt, "vol_target_pct"), 15.0))
        except Exception:
            pass

        # Defaults (non-mutating reads)
        bt.walkforward_splits = _to_int(getattr(bt, "walkforward_splits", 3), 3)
        bt.initial_cash = _to_float(getattr(bt, "initial_cash", 100_000.0), 100_000.0)
        bt.vol_target = _to_float(getattr(bt, "vol_target", 15.0), 15.0)

    # Data defaults
    data = getattr(cfg, "data", None)
    if data is not None:
        try:
            if not hasattr(data, "symbol"):
                setattr(data, "symbol", "BTC-USD")
            if not hasattr(data, "source"):
                setattr(data, "source", "yfinance")
            if not hasattr(data, "interval"):
                setattr(data, "interval", "1d")
            if not hasattr(data, "start"):
                setattr(data, "start", _dt.date(2020, 1, 1))
            if not hasattr(data, "end"):
                setattr(data, "end", None)
        except Exception:
            pass

    return cfg


# -------------- Sidebar --------------
def _sidebar(cfg, ns: str) -> Any:
    """
    Renders the sidebar for a given namespace (ns).
    Each tab/screen must provide its own ns to guarantee unique widget keys.
    """
    cfg = _ensure_cfg_compat(cfg)

    with st.sidebar:
        st.header("Data")

        # symbol
        val_symbol = st.text_input(
            "Symbol",
            value=str(getattr(cfg.data, "symbol", "BTC-USD")),
            key=_k(ns, "symbol"),
        )
        try:
            cfg.data.symbol = val_symbol
        except Exception:
            pass

        # source
        source_opts = ["yfinance", "csv", "parquet"]
        cur_source = getattr(cfg.data, "source", "yfinance")
        source_idx = source_opts.index(cur_source) if cur_source in source_opts else 0

        val_source = st.selectbox(
            "Source",
            options=source_opts,
            index=source_idx,
            key=_k(ns, "source"),
        )
        try:
            cfg.data.source = val_source
        except Exception:
            pass

        # interval
        interval_opts = ["1d", "1h", "15m"]
        cur_interval = getattr(cfg.data, "interval", "1d")
        interval_idx = interval_opts.index(cur_interval) if cur_interval in interval_opts else 0

        val_interval = st.selectbox(
            "Interval",
            options=interval_opts,
            index=interval_idx,
            key=_k(ns, "interval"),
        )
        try:
            cfg.data.interval = val_interval
        except Exception:
            pass

        # dates
        val_start = st.date_input(
            "Start",
            value=_to_date(getattr(cfg.data, "start", _dt.date(2020, 1, 1))),
            key=_k(ns, "start"),
        )
        val_end = st.date_input(
            "End",
            value=_to_date(getattr(cfg.data, "end", None)),
            key=_k(ns, "end"),
        )
        try:
            cfg.data.start = val_start
            cfg.data.end = val_end
        except Exception:
            pass

        st.divider()
        st.header("Fees & Slippage")

        # Handle via getattr defaults and avoid crashing on frozen dataclasses
        comm_bps_default = getattr(cfg.fees, "commission_bps", getattr(getattr(cfg, "_ui_overrides", {}), "commission_bps", 0) if hasattr(cfg, "_ui_overrides") else 0)
        slip_bps_default = getattr(cfg.fees, "slippage_bps", getattr(getattr(cfg, "_ui_overrides", {}), "slippage_bps", 0) if hasattr(cfg, "_ui_overrides") else 0)

        val_comm = int(
            st.number_input(
                "Commission (bps)",
                value=int(_to_int(comm_bps_default, 0)),
                step=1,
                key=_k(ns, "commission_bps"),
            )
        )
        val_slip = int(
            st.number_input(
                "Slippage (bps)",
                value=int(_to_int(slip_bps_default, 0)),
                step=1,
                key=_k(ns, "slippage_bps"),
            )
        )
        try:
            cfg.fees.commission_bps = val_comm
            cfg.fees.slippage_bps = val_slip
        except Exception:
            # store in session for pipeline to read if needed
            st.session_state[_k(ns, "commission_bps_val")] = val_comm
            st.session_state[_k(ns, "slippage_bps_val")] = val_slip

        st.divider()
        st.header("Backtest")

        val_wf = int(
            st.number_input(
                "Walk-forward splits",
                value=int(getattr(cfg.bt, "walkforward_splits", 3)),
                min_value=1,
                step=1,
                key=_k(ns, "wf_splits"),
            )
        )
        val_cash = float(
            st.number_input(
                "Initial Cash",
                value=float(getattr(cfg.bt, "initial_cash", 100_000.0)),
                step=1000.0,
                key=_k(ns, "initial_cash"),
            )
        )
        val_vol = float(
            st.number_input(
                "Vol Target (annual, %)",
                value=float(getattr(cfg.bt, "vol_target", 15.0)),
                step=1.0,
                key=_k(ns, "vol_target"),
            )
        )
        try:
            cfg.bt.walkforward_splits = val_wf
            cfg.bt.initial_cash = val_cash
            cfg.bt.vol_target = val_vol
        except Exception:
            st.session_state[_k(ns, "wf_splits_val")] = val_wf
            st.session_state[_k(ns, "initial_cash_val")] = val_cash
            st.session_state[_k(ns, "vol_target_val")] = val_vol

    return cfg


# -------------- Strategy param forms --------------
def _strategy_params(ns: str, strategy: str) -> Dict[str, Any]:
    """
    Returns a dict of params for the selected strategy using namespaced keys.
    """
    params: Dict[str, Any] = {}
    if strategy == "ma_crossover":
        c1, c2 = st.columns(2)
        params["ma_fast"] = int(c1.number_input("MA Fast", value=20, step=1, key=_k(ns, "ma_fast")))
        params["ma_slow"] = int(c2.number_input("MA Slow", value=50, step=1, key=_k(ns, "ma_slow")))
    elif strategy == "ai_unified":
        models = list_models() or []
        default_idx = 0 if models else -1
        params["model_name"] = st.selectbox(
            "AI Model",
            options=models,
            index=default_idx,
            key=_k(ns, "ai_model"),
        )
        params["threshold"] = float(
            st.number_input("Threshold", value=0.5, step=0.05, key=_k(ns, "ai_threshold"))
        )
    # add other strategies here with unique keys under ns
    return params


# -------------- Main pages --------------
def _page_run():
    ns = "run"
    cfg = _sidebar(load_config(), ns=ns)

    st.subheader("Strategy")
    strategies = list_strategies() or []
    if not strategies:
        st.warning("No strategies registered. Please check your registry.")
        return

    strat = st.selectbox(
        "Select Strategy",
        options=strategies,
        index=0,
        key=_k(ns, "strategy"),
    )
    params = _strategy_params(ns, strat)

    if st.button("Run Backtest", type="primary", key=_k(ns, "run_btn")):
        try:
            df, info = run_pipeline(strat, params=params, cfg=cfg)
            st.success("Backtest completed.")
            eq = info.get("equity")
            if isinstance(eq, (pd.Series, pd.DataFrame)):
                st.line_chart(eq)
            stats = info.get("stats", {})
            if isinstance(stats, dict) and stats:
                st.dataframe(pd.DataFrame([stats]))
            st.session_state[_k("state", "last_info")] = info
        except Exception as e:
            st.error(f"Run failed: {e}")


def _page_compare():
    ns = "compare"
    cfg = _sidebar(load_config(), ns=ns)

    st.subheader("Compare AI models")
    models = list_models() or []
    default_selection = models[:2] if models else []
    selected = st.multiselect(
        "Models",
        options=models,
        default=default_selection,
        key=_k(ns, "models"),
    )

    if st.button("Run Compare", key=_k(ns, "compare_btn")):
        rows: List[Dict[str, Any]] = []
        for m in selected:
            try:
                _, info = run_pipeline("ai_unified", params={"model_name": m, "threshold": 0.5}, cfg=cfg)
                stats = info.get("stats", {})
                if isinstance(stats, dict) and stats:
                    rows.append({"model": m, **stats})
            except Exception as e:
                st.error(f"{m}: {e}")
        if rows:
            df_metrics = pd.DataFrame(rows)
            sort_col = "sharpe" if "sharpe" in df_metrics.columns else df_metrics.columns[1]
            st.dataframe(df_metrics.sort_values(sort_col, ascending=False, ignore_index=True))


def _page_report():
    ns = "report"
    st.subheader("Report (last run)")
    info = st.session_state.get(_k("state", "last_info"))
    if info:
        stats = info.get("stats", {})
        eq = info.get("equity")
        if isinstance(stats, dict) and stats:
            st.dataframe(pd.DataFrame([stats]), use_container_width=True)
        if isinstance(eq, (pd.Series, pd.DataFrame)):
            st.line_chart(eq)
    else:
        st.info("Run a backtest first.")


# -------------- Public entry --------------
def show_main():
    st.set_page_config(page_title="Autonom Trading", layout="wide")
    st.title(APP_TITLE)

    tabs = st.tabs(["Run", "Compare", "Report"])
    with tabs[0]:
        _page_run()
    with tabs[1]:
        _page_compare()
    with tabs[2]:
        _page_report()

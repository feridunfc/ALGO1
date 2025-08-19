# Project Status Index — v2.5 Track (Hotfix 2.9.13: Data + AI Models)

**Generated:** 2025-08-17T14:42:52.670396Z

This file is the *single source of truth* to check before modifying code. Keep it in the repo root.
Mark items below as **FROZEN** when we agree they must not be edited in hotfixes.

---

## ✅ Completed & FROZEN (do NOT modify in hotfixes)
- **EventBus & Events** (`src/core/event_bus.py`, `src/core/events/*`)
  - Priority, sticky, request/response, DLQ, retries, dynamic workers, tracing hooks.
- **Enhanced Risk Engine** (`src/core/enhanced_risk_engine.py`)
  - Regime-aware consensus, circuit breakers, position sizing.
- **Backtest Engine** (`src/core/backtest_engine.py`)
  - 1-bar delay, commission/slippage models, multi-asset portfolio.
- **Data Normalizer** (`src/core/data_normalizer.py`)
  - NaN policies, ZScore/MinMax/Robust, rolling mode, leakage guards.
- **UI (Streamlit)** (`ui/st_tabs.py`)
  - Namespaced keys, config compatibility shim, Run/Compare/Report tabs.

> Note: These are considered **production-grade** and compliant with quant-engineering best practices.
> Changes must be done via RFC + review, *not* directly in hotfixes.

---

## 🟡 Newly Added in this Hotfix (Data + AI Models)
- **Model Registry** (`src/core/models/registry.py`)
  - Simple decorator/registry for ML models, used by UI and strategies.
- **XGBoost Model Adapter** (`src/core/models/xgb_model.py`)
  - Graceful fallback if `xgboost` is unavailable.
- **RandomForest Model Adapter** (`src/core/models/rf_model.py`)
- **AI Unified Strategy** (`src/core/strategies/ai_unified.py`)
  - Model-agnostic, thresholded signal mapping (-1/0/1), leakage-safe vectorized predict.
- **Data Loader (normalized)** (`src/data/loader.py`)
  - Pulls yfinance/CSV/Parquet, enforces **FinancialDataNormalizer**.
- **Feature Pipeline** (`src/features/feature_pipeline.py`)
  - Leakage-free TA features (returns/lag/MA/RSI/ATR) with strict shift rules.
- **Walk-Forward Runner** (`src/backtesting/walk_forward.py`)
  - TimeSeriesSplit with per-fold training and backtest adapter hooks.
- **Backtest Adapter** (`src/backtesting/adapter.py`)
  - Converts vectorized signals to orders (T+1), uses BacktestEngine; safe fallback if engine missing.
- **Pipeline Orchestrator** (`src/pipeline/orchestrator.py`)
  - Glue for UI: load → normalize → features → signals → backtest → metrics.

All new modules are **open for iteration** in v2.5 sprint. Unit tests & CI are recommended next.

---

## 🎯 Compliance with Industry Standards
- **Data integrity & leakage**: standardized columns, timezone-aware indices, strict `.shift(1)` on features.
- **Reproducibility**: seedable training; walk-forward split (no shuffle).
- **Execution realism**: T+1 open, slippage/commission modeling via BacktestEngine.
- **Extensibility**: registry-based models/strategies; orchestrator decoupled from UI.

---

## 🔜 Next (v2.5 sprint goals)
- Per-fold metrics (Sharpe/Sortino/Calmar/MaxDD) aggregation in `walk_forward.py`.
- Golden tests for normalizer and AI pipeline with synthetic data.
- Experiment logging (params.json + metrics.json per run).
- Compare tab to consume WF summaries directly.
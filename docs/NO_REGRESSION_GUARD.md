This hotfix is **additive-only** and does not overwrite frozen modules.

**Frozen list (as per ROOT_STATUS_LOCK.md)**:
- core/event_bus.py
- core/data_normalizer.py (and Normalization contract)
- backtest/engine.py (T+1, cost model, trade dataclass)
- core/enhanced_risk_engine.py (ERE)
- ui/st_tabs.py (namespaced keys + _ensure_cfg_compat)
- backtest/walk_forward_runner.py
- experiments/tracking.py

Added components live under *_ext/ and `ui/pages/02_Compare_WF_HPO.py` to avoid touching frozen files.
To launch without modifying existing entrypoints:
  `streamlit run ui/run_bootstrap.py`

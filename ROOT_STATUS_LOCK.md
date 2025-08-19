# ROOT_STATUS_LOCK.md
Bu dosya **kilit/rehber** dosyadır. Değiştirmeyin. (FROZEN)

## FROZEN (değişmeyecek) modüller
- Event Bus & Event Sınıfları
- EnhancedRiskEngine (core/enhanced_risk_engine.py)
- BacktestEngine (core/backtest_engine.py)
- DataNormalizer (core/data_normalizer.py)
- UI: ui/st_tabs.py (namespaced key fix ile)

## Bu patch’in ekledikleri (v2.5 Hotfix — Data & AI tamamlayıcı)
- experiments/tracking.py — Basit, dosya tabanlı experiment tracking
- backtesting/walk_forward.py — Per-fold metrikli Walk-Forward Runner
- optimization/hpo_optuna.py — Optuna HPO (opsiyonel, yoksa stub)
- core/risk/portfolio_constraints.py — Max allocation / sector cap / corr cap
- risk/anomaly_bridge.py — Anomali & sentiment → position size çarpanı
- pipeline/runner.py — Orchestrator uyumlu koşu yardımcıları
- tests/golden/test_wf_metrics.py — WF metrik smoke testi
- tests/golden/test_normalizer_contract.md — Normalizer sözleşme maddeleri

## Entegrasyon rehberi
- UI `run_pipeline` çağrısı kalabilir. Alternatif yeni giriş noktaları:
  - `from pipeline.runner import run_backtest_single, run_walk_forward, run_hpo_study`
- RiskEngine ile köprü: `risk/anomaly_bridge.py` ve `core/risk/portfolio_constraints.py`
- Experiment tracking: `experiments/tracking.py` kullanın

## Versiyon uyumluluğu
- Python >=3.9, pandas>=2.0, numpy>=1.24, scikit-learn>=1.3
- Optuna opsiyoneldir (yoksa stub çalışır).


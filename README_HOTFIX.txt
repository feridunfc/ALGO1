HOTFIX v2.9 — Streamlit + Metric + Slippage + Strategy Bootstrap
================================================================

Neler düzeltiliyor?
- streamlit_app.py: _page_config hatası kaldırıldı, sağlam sayfa linkleri ve asyncio event loop guard eklendi.
- ui/components/metric_card.py: Eski Streamlit sürümleriyle uyumlu; `label_visibility` gibi bilinmeyen argümanları yutuyor.
- src/core/slippage/volume_weighted.py: `from __future__` en üste alındı. VWAP/ADV tabanlı iki fonksiyon sağlandı.
- src/strategies/plugins/auto_register.py: Stratejileri otomatik keşfedip STRATEGY_REGISTRY'ye basar.

Kurulum
1) Zip'i repo köküne açın (dosyalar var olan path'lere yazılır).
2) Hızlı testler:
   - Slippage:
     python -c "import sys;sys.path.insert(0,'.');from src.core.slippage.volume_weighted import apply_vwap_slippage;print(apply_vwap_slippage(100.0,'BUY',10_000,1_000_000))"
     # Beklenen: (100.1, 10.0)
   - Strategy registry:
     python -c "import sys;sys.path.insert(0,'.');from src.strategies.plugins.auto_register import bootstrap;print('count=',len(bootstrap(verbose=True)))"
3) Streamlit:
   streamlit run streamlit_app.py

Git
  git add -A
  git commit -m "hotfix: Streamlit metric guard + slippage future-import + strategy bootstrap"
  git push

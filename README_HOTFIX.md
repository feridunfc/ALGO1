# Revize Edilmiş v2.5/v2.6 Uygulama Hotfix (Tek Paket)

Bu paket DataPipeline (strict), Walk-Forward Motoru, Risk Zinciri, HPO ve UI entegrasyonlarını **tek hotfix** olarak ekler.

## Kurulum
1) ZIP'i repo köküne açın (src/, ui/, config/, tests/, .github/).
2) Gerekli paketler: pandas, numpy, scikit-learn, streamlit, pydantic, optuna, pytest (ve opsiyonel pyarrow).

## Test
```bash
pytest -q tests/golden/test_normalizer.py
pytest -q tests/smoke/test_wf_engine.py
```

## UI
```bash
streamlit run ui/backtest_page.py
```

## Notlar
- Golden doğrulama hash'i `config/golden_data_hash.json` içinde. `ENV=production` iken DataPipeline işleme sonunda hash eşitliğini doğrular.
- Risk ayarları `config/config.json` üzerinden UI ile güncellenebilir (sidebar).

# 2.9.13 UI/NLP/Anomaly Hotfix (2025-08-16T19:13:07.094411Z)

This archive contains:
- `ui/st_tabs.py`: Streamlit hotfix with unique keys and config-compat guard (fixes DuplicateElementId & missing `commission_bps`).
- `src/nlp/*`: Sentiment analyzer (HF transformers with safe fallback), news feeder stub, preprocessor.
- `src/anomaly/*`: IsolationForest-based detector, dynamic thresholds, alert handler.
- `src/utils/nlp_utils.py`: tiny helper.

## Usage
1. Drop `ui/st_tabs.py` into your repo (replace existing).
2. Merge `src/nlp`, `src/anomaly`, `src/utils` into your `src/` tree.
3. Optional deps:
   ```bash
   pip install transformers feedparser tweepy scikit-learn
   ```
4. Run Streamlit app as usual.

## Notes
- The UI avoids duplicate widget IDs by namespacing keys per tab.
- If your `FeesConfig` is frozen or missing `commission_bps/slippage_bps`, the UI reads defaults safely without crashing.
- If you cannot mutate config objects, the entered values are kept in `st.session_state` under namespaced keys.


v1.4 adds Rich HTML reporting:
- Equity, Drawdown, Rolling Sharpe charts
- Monthly returns heatmap
- Assets ranking table
- Strategy compare table (if run)
- Sentiment/Macro snapshots (stubbed series)
- Optional QuantStats one-click report (if quantstats is installed).

How to apply:
- Copy `src/` from backend_patch_v1_4_* into your project `src/` (or just merge analytics/ and pipeline/).
- Replace your UI's `st_tabs.py` with the provided one so the Report tab renders HTML.

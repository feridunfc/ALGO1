
This package:
- Adds sitecustomize.py (Windows/Streamlit event loop safety)
- Provides full Streamlit multipage UI (Home, Single, Compare, HPO, History, Error Console, RealTime, Anomaly)
- Keeps metric labels accessible (no empty label)
- Includes services_ext runner bridge + charts
- Intended to be used together with v2.7b risk/signal/wf/hpo modules (or copy those under src/ and backtest_ext/).

Run:
    pip install -r requirements.txt
    streamlit run streamlit_app.py

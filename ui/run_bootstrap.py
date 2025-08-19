import asyncio, sys
from pathlib import Path
import importlib

# Ensure ROOT & src on path (redundant to sitecustomize, but safe if not loaded)
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
for p in (str(ROOT), str(SRC)):
    if p not in sys.path:
        sys.path.insert(0, p)

# Event loop policy for Windows/Py3.12
try:
    if sys.platform.startswith("win"):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
except Exception:
    pass
try:
    asyncio.get_running_loop()
except RuntimeError:
    try:
        asyncio.set_event_loop(asyncio.new_event_loop())
    except Exception:
        pass

import streamlit as st

def main():
    st.set_page_config(layout="wide", page_title="Quant UI (Bootstrap)", page_icon="📊")
    st.sidebar.success("Bootstrap aktif (no-regression)")
    # Try user app
    try:
        app = importlib.import_module("ui.streamlit_app")
        if hasattr(app, "main"):
            app.main()
            return
    except Exception as e:
        st.warning(f"User UI yüklenemedi: {e}")
    # Fallback: safe compare page
    try:
        from ui.pages.compare_safe import render as compare_render
    except Exception as e:
        st.error(f"Güvenli compare sayfası import hatası: {e}")
        return
    compare_render()

if __name__ == "__main__":
    main()

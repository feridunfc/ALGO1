import streamlit as st

# --- Page config & landing ---
st.set_page_config(page_title="Algo Trading Suite", page_icon="🤖", layout="wide")
st.title("🤖 Otonom Algo-Trade Platformu")
st.write("Soldaki **Pages** menüsünden odaları açın.")

# --- Quick page links (guarded) ---
try:
    st.page_link("pages/01_Single_Run.py", label="🚀 Tekli Çalıştırma", icon="🚀")
    st.page_link("pages/02_Compare.py", label="⚖️ Strateji Karşılaştırma", icon="⚖️")
    st.page_link("pages/03_HPO.py", label="⚙️ Optimizasyon (HPO)", icon="⚙️")
    st.page_link("pages/04_History.py", label="📜 Geçmiş Sonuçlar", icon="📜")
    st.page_link("pages/05_ErrorConsole.py", label="🧯 Error Console", icon="🧯")
    st.page_link("pages/06_RealTimeMonitor.py", label="🛰️ Real-Time Monitor", icon="🛰️")
    st.page_link("pages/07_AnomalyDetector.py", label="🧭 Anomali/Sentiment", icon="🧭")
    st.page_link("pages/08_Paper_Trading.py", label="📄 Paper Trading", icon="📄")
    st.page_link("pages/09_Risk_Dashboard.py", label="📊 Risk Dashboard", icon="📊")
    st.page_link("pages/10_Committee_Simulator.py", label="🧠 Committee Simulator", icon="🧠")
except Exception as e:
    st.warning(f"Sayfa linkleri yüklenemedi: {e}")

# --- asyncio event loop guard ---
import asyncio
try:
    asyncio.get_event_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())

# --- Strategy registry bootstrap (best-effort) ---
try:
    from src.strategies.plugins.auto_register import bootstrap as _register_strategies
    _register_strategies()
except Exception as e:
    st.warning(f"Strateji kayıtları yüklenemedi: {e}")

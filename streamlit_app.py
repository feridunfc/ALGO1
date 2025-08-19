# streamlit_app.py (en üstte)
# streamlit_app.py
import streamlit as st
st.set_page_config(page_title="Algo Trading Suite", page_icon="🤖", layout="wide")

from src.strategies.registry import bootstrap, list_strategies
added = bootstrap(mode="auto")  # önce auto_register, olmazsa statik bağlar
st.sidebar.info(f"📦 Strateji sayısı: {len(list_strategies())} (+{added})")


# --- Strategy registry bootstrap (auto-discovery) ---
loaded_delta = 0
try:
    from src.strategies.plugins.auto_register import bootstrap
    loaded_delta = bootstrap()
    st.sidebar.success(f"📦 Strateji kayıtları: +{loaded_delta}")
except Exception as e:
    st.sidebar.warning(f"Strateji kayıtları yüklenemedi: {e}")

st.title("🤖 Otonom Algo-Trade Platformu")
st.write("Soldaki **Pages** menüsünden odaları açın.")

# Hızlı linkler
for pth, label, icon in [
    ("pages/01_Single_Run.py", "🚀 Tekli Çalıştırma", "🚀"),
    ("pages/02_Compare.py", "⚖️ Strateji Karşılaştırma", "⚖️"),
    ("pages/03_HPO.py", "⚙️ Optimizasyon (HPO)", "⚙️"),
    ("pages/04_History.py", "📜 Geçmiş Sonuçlar", "📜"),
]:
    try:
        st.page_link(pth, label=label, icon=icon)
    except Exception:
        pass

# asyncio guard
import asyncio
try:
    asyncio.get_event_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())


import streamlit as st
from ui.components.backend_console import render as console_render
st.set_page_config(layout="wide", page_title="Error Console", page_icon="🧯")
st.title("🧯 Error Console")
lvl = st.selectbox("Level", ["ALL","INFO","WARNING","ERROR"], index=0)
strategy = st.text_input("Strategy filter", "")
console_render("Logs", None if lvl=="ALL" else lvl, strategy if strategy else None)

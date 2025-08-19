import streamlit as st
from typing import Optional

def metric_card(label: str, value: str, delta: Optional[str]=None, help: Optional[str]=None):
    """
    Streamlit >= 1.32: boş label kullanma uyarısını engeller.
    """
    safe_label = label or "—"
    st.metric(label=safe_label, value=value, delta=delta, help=help, label_visibility="visible")

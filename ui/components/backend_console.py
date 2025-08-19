
import streamlit as st
from collections import deque
from datetime import datetime
KEY = "backend_console_logs"
def _init(maxlen: int = 1000):
    if KEY not in st.session_state:
        st.session_state[KEY] = deque(maxlen=maxlen)
def log(message: str, level: str = "INFO", strategy: str | None = None):
    _init()
    ts = datetime.now().strftime("%H:%M:%S")
    prefix = f"[{ts}] [{level}]"
    if strategy: prefix += f" [{strategy}]"
    st.session_state[KEY].appendleft(f"{prefix} {message}")
def render(title: str = "Backend Console", level_filter: str | None = None, strategy_filter: str | None = None):
    _init()
    with st.expander(title, expanded=False):
        logs = list(st.session_state[KEY])
        if level_filter and level_filter != "ALL":
            logs = [l for l in logs if f"[{level_filter.upper()}]" in l]
        if strategy_filter:
            logs = [l for l in logs if f"[{strategy_filter}]" in l]
        st.code("\n".join(logs[:300]) if logs else "No logs.", language="text")

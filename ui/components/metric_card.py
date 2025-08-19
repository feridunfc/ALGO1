from __future__ import annotations
from typing import Optional, Any
import streamlit as st

def metric_card(
    label: str,
    value: Any,
    delta: Optional[Any] = None,
    help: Optional[str] = None,
    **kwargs
) -> None:
    """
    Backward-compatible metric widget.
    - Ignores unknown kwargs like `label_visibility` to avoid TypeError on older Streamlit.
    - Falls back to st.metric without `help` if running on very old versions.
    """
    # remove unsupported args gracefully
    kwargs.pop("label_visibility", None)
    try:
        st.metric(label=label, value=value, delta=delta, help=help)
    except TypeError:
        # older Streamlit without `help` param
        st.metric(label=label, value=value, delta=delta)

__all__ = ["metric_card"]

import streamlit as st
from ..services.runners import run_single, run_walk_forward

class BacktestPanel:
    def render(self):
        st.selectbox("Mode", ["Single", "Walk-Forward"], key="ns_backtest_mode")

        if st.session_state.ns_backtest_mode == "Walk-Forward":
            self._render_wf_controls()
        else:
            if st.button("Run Single", key="ns_run_single"):
                try:
                    res = run_single()
                    st.success("Done.")
                    st.dataframe(res.summary if hasattr(res, "summary") else res)
                except Exception as e:
                    st.session_state.ns_last_error = str(e)
                    st.rerun()

        if st.session_state.get("ns_last_error"):
            st.error(f"Execution failed: {st.session_state.ns_last_error}")
            log = st.session_state.ns_last_error.encode()
            st.download_button("Download Error Log", log, file_name="error.log")

    def _render_wf_controls(self):
        c1, c2, c3 = st.columns(3)
        c1.number_input("Folds", 3, 10, 5, key="ns_wf_folds")
        c2.number_input("Test Days", 21, 252, 63, key="ns_wf_test_days")
        c3.number_input("Gap (days)", 0, 10, 1, key="ns_wf_gap")

        if st.button("Run WF", key="ns_wf_run"):
            try:
                results = run_walk_forward(
                    n_splits=st.session_state.ns_wf_folds,
                    test_size=st.session_state.ns_wf_test_days,
                    gap=st.session_state.ns_wf_gap
                )
                st.dataframe(results.summary)
                st.download_button("Download CSV",
                    data=results.summary.to_csv().encode(),
                    file_name="wf_results.csv",
                    mime="text/csv")
            except Exception as e:
                st.session_state.ns_last_error = str(e)
                st.rerun()

# src/core/validators/lookahead.py
import pandas as pd

class LookaheadValidator:
    """Simple guard: ensures strictly increasing timestamps (no duplicates) and no backward jumps.
    This targets 'time order' rather than feature leakage at this stage.
    """
    def validate(self, df: pd.DataFrame) -> None:
        if not isinstance(df.index, pd.DatetimeIndex):
            raise TypeError("LookaheadValidator: DatetimeIndex required")
        if not df.index.is_monotonic_increasing:
            raise ValueError("LookaheadValidator: Non-monotonic timestamps detected")
        if df.index.has_duplicates:
            raise ValueError("LookaheadValidator: Duplicate timestamps detected")

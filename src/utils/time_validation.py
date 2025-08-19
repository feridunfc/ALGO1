
import pandas as pd
import numpy as np

class TimeValidator:
    def __init__(self, max_lag_ms: int = 100):
        self.max_lag = pd.Timedelta(max_lag_ms, 'ms')

    def check_event_sequence(self, events):
        if not events:
            return {'is_ordered': True, 'max_lag_ms': 0, 'is_valid': True}
        ts = [e.timestamp for e in events]
        is_sorted = all(ts[i] <= ts[i+1] for i in range(len(ts)-1))
        tsv = pd.Series(ts).astype('datetime64[ns]')
        diffs = tsv.diff().dropna().values.astype('timedelta64[ms]').astype(float)
        max_lag = float(diffs.max()) if len(diffs) else 0.0
        return {
            'is_ordered': is_sorted,
            'max_lag_ms': max_lag,
            'is_valid': is_sorted and max_lag < self.max_lag / pd.Timedelta(1, 'ms')
        }

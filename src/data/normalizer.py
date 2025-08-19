import pandas as pd
import numpy as np
import warnings

class DataNormalizer:
    def __init__(self, config=None, nan_policy='drop', leakage_test=True):
        self.config = config or {'mappings': {'Adj Close': 'close'}, 'scaling_method': 'zscore', 'fit_window': 252}
        self.nan_policy = nan_policy
        self.leakage_test = leakage_test
        self._fit_params = {}

    def normalize(self, data: pd.DataFrame) -> pd.DataFrame:
        data = data.rename(columns=self.config['mappings'])
        if self.nan_policy == 'drop':
            data = data.dropna()
        elif self.nan_policy == 'ffill':
            data = data.ffill().dropna()
        elif self.nan_policy == 'interpolate':
            data = data.interpolate().dropna()
        if self.leakage_test:
            self._check_lookahead_bias(data)
        if self.config.get('scaling_method') == 'zscore':
            return self._zscore_normalize(data)
        elif self.config.get('scaling_method') == 'minmax':
            return self._minmax_normalize(data)
        return data

    def _zscore_normalize(self, data: pd.DataFrame) -> pd.DataFrame:
        if not self._fit_params:
            self._fit_params = {
                col: {'mean': data[col].rolling(self.config['fit_window']).mean(),
                      'std': data[col].rolling(self.config['fit_window']).std()}
                for col in data.columns
            }
        normalized = pd.DataFrame(index=data.index)
        for col in data.columns:
            mean = self._fit_params[col]['mean']
            std = self._fit_params[col]['std'].replace(0, 1e-6)
            normalized[col] = (data[col] - mean) / std
        return normalized.dropna()

    def _minmax_normalize(self, data: pd.DataFrame) -> pd.DataFrame:
        normalized = (data - data.min()) / (data.max() - data.min()).replace(0,1e-6)
        return normalized.dropna()

    def _check_lookahead_bias(self, data: pd.DataFrame):
        for col in data.columns:
            if data[col].isnull().any():
                warnings.warn(f"Potential lookahead bias in column {col}")

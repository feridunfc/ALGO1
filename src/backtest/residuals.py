
import numpy as np
import pandas as pd

try:
    import statsmodels.api as sm
    from scipy import stats
except Exception:
    sm = None
    stats = None

class ResidualAnalyzer:
    def analyze(self, strategy_returns: pd.Series, benchmark_returns: pd.Series):
        residuals = (strategy_returns - benchmark_returns).dropna()
        out = {'is_normal': None, 'autocorrelation': None, 'stationary': None}
        if len(residuals) < 10:
            return out
        if stats is not None:
            _, p_normal = stats.shapiro(residuals.sample(min(500, len(residuals)), random_state=42))
            out['is_normal'] = bool(p_normal > 0.05)
        if sm is not None:
            acf = sm.tsa.stattools.acf(residuals.values, nlags=min(5, len(residuals)-1), fft=True)
            out['autocorrelation'] = acf[1:].tolist()
            try:
                p_adf = sm.tsa.adfuller(residuals.values, autolag='AIC')[1]
                out['stationary'] = bool(p_adf < 0.05)
            except Exception:
                out['stationary'] = None
        return out

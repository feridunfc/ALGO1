import numpy as np, pandas as pd
from backtesting.walk_forward import WalkForwardRunner

class DummyStrat:
    def __init__(self, bias=0.0):
        self.bias = bias
    def train(self, X, y=None):
        pass
    def predict_signals(self, X):
        # simple moving sign of momentum with bias
        mom = X['close'].diff().fillna(0.0)
        sig = np.sign(mom + self.bias).clip(-1,1)
        return pd.Series(sig, index=X.index)

def test_wf_smoke():
    np.random.seed(42)
    n=260
    prices = pd.Series(np.cumprod(1+0.001+0.02*np.random.randn(n)), index=pd.date_range('2022-01-01', periods=n, freq='B'), name='close')
    feat = pd.DataFrame({'close': prices})
    runner = WalkForwardRunner(n_splits=4)
    df, summary = runner.run(feat, prices, DummyStrat, {'bias':0.0})
    assert df.shape[0] == 4
    assert 'sharpe' in df.columns
    assert isinstance(summary.get('mean_sharpe', 0.0), float)

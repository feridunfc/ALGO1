# engines/market_regime_detector.py
import numpy as np, pandas as pd
from typing import Optional
from utils.app_logger import get_app_logger

try:
    from hmmlearn.hmm import GaussianHMM
    HMM_OK = True
except ImportError:
    GaussianHMM = None
    HMM_OK = False

class MarketRegimeDetector:
    def __init__(self, n_states: int = 3, vol_lb: int = 20, use_hmm: Optional[bool] = None):
        self.n_states = n_states
        self.vol_lb = vol_lb
        self.use_hmm = HMM_OK if use_hmm is None else use_hmm
        self.hmm: Optional[GaussianHMM] = None
        self.log = get_app_logger("MarketRegime")

    def add_regime(self, df: pd.DataFrame) -> pd.DataFrame:
        out = df.copy()
        ret = out["close"].pct_change().fillna(0.0)
        vol = ret.rolling(self.vol_lb).std().fillna(ret.std())
        feats = np.column_stack([ret.values, vol.values])

        if self.use_hmm:
            try:
                self.hmm = GaussianHMM(n_components=self.n_states, covariance_type="full", n_iter=200, random_state=42)
                self.hmm.fit(feats)
                states = self.hmm.predict(feats)
                post = self.hmm.predict_proba(feats)
                out["regime"] = states
                out["regime_prob"] = post.max(axis=1)
                return out
            except Exception as e:
                self.log.warning(f"HMM başarısız → quantile mod: {e}")

        # Fallback: vol quantiles
        q = np.nanpercentile(vol, [33, 66])
        states = np.where(vol <= q[0], 0, np.where(vol <= q[1], 1, 2))
        # Prob ~ mesafe tabanlı kaba yaklaşım
        dist0 = np.abs(vol - q[0]); dist1 = np.abs(vol - q[1])
        denom = (dist0 + dist1).replace(0, np.nan)
        prob = 1.0 - (np.minimum(dist0, dist1) / denom).fillna(1.0)
        out["regime"] = states.astype(int)
        out["regime_prob"] = prob.values
        return out

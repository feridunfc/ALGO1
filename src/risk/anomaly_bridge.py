from __future__ import annotations
from typing import Optional

class AnomalySentimentSizer:
    """Anomali şiddeti ve sentiment skorunu pozisyon boyutuna çeviren çarpan.
    severity: [0..1], sentiment: [-1..+1]
    """
    def __init__(self,
                 max_cut: float = 0.7,     # çok kötü durumda %70 küçült
                 boost: float = 0.2,       # çok iyi sentimentte %20 büyüt
                 neutral_sent: float = 0.15):
        self.max_cut = max_cut
        self.boost = boost
        self.neutral_sent = neutral_sent

    def multiplier(self, severity: float = 0.0, sentiment: float = 0.0) -> float:
        # anomaly reduces, sentiment can boost on the margin
        cut = severity * self.max_cut   # 0..max_cut
        extra = 0.0
        if sentiment > self.neutral_sent:
            extra = (sentiment - self.neutral_sent) * self.boost
        m = (1.0 - cut) * (1.0 + extra)
        # clamp
        return max(0.1, min(1.25, m))

    def apply(self, base_weight: float, severity: float = 0.0, sentiment: float = 0.0) -> float:
        return base_weight * self.multiplier(severity, sentiment)

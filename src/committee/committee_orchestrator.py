from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Callable

@dataclass
class CommitteeConfig:
    regime_overrides: Dict[str, dict] | None = None

class CommitteeOrchestrator:
    """
    AS → Regime → ERE → PC → TE akışını tek yerde koşturur.
    Çekirdek motorlara dokunmadan adapter ile bağlanır.
    """
    def __init__(self, asset_selector, regime_detector, ere_adapter,
                 portfolio_constructor, trade_executor, cfg: CommitteeConfig | None = None):
        self.asset_selector = asset_selector
        self.regime_detector = regime_detector
        self.ere = ere_adapter
        self.pc = portfolio_constructor
        self.te = trade_executor
        self.cfg = cfg or CommitteeConfig(regime_overrides={})

    def run_once(self, feature_provider: Callable[[str], dict] | None = None,
                 current_weights: Dict[str, float] | None = None):
        # 1) evren
        U = self.asset_selector.universe()
        # 2) rejim
        regime = self.regime_detector.current()
        # 3) rejime göre cap override
        if regime in (self.cfg.regime_overrides or {}):
            over = self.cfg.regime_overrides[regime]
            if "max_allocation_per_asset" in over:
                self.pc.cfg.max_allocation_per_asset = over["max_allocation_per_asset"]
        # 4) ERE kararları
        allowed = {}
        for s in U:
            feats = feature_provider(s) if feature_provider else {}
            dec = self.ere.assess(s, feats)
            if dec.allowed and dec.position_size_pct > 0:
                allowed[s] = dec.position_size_pct
        # 5) portföy
        target = self.pc.construct(allowed)
        # 6) emirler
        current_weights = current_weights or {}
        orders = self.te.diff(current_weights, target)
        return {"regime": regime,
                "universe": U,
                "target": target,
                "orders": [o.__dict__ for o in orders]}

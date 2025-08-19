from typing import List
from pydantic import BaseModel, Field
from dataclasses import dataclass

class RiskConfig(BaseModel):
    market_regime_rejection_threshold: float = Field(0.4, ge=0.0, le=1.0)
    min_adv_pct: float = Field(0.01, gt=0.0)
    max_allocation_per_asset: float = Field(0.2, gt=0.0, le=1.0)
    max_correlation: float = Field(0.7, gt=0.0, le=1.0)

@dataclass
class RiskContext:
    symbol: str
    features: dict
    sentiment_score: float
    anomaly_score: float
    adv_pct: float
    proposed_weight: float
    corr_matrix: object = None
    sector: str = "unknown"

@dataclass
class RiskDecision:
    ok: bool
    reason: str = ""
    weight: float = 0.0
    @staticmethod
    def reject(reason: str) -> "RiskDecision":
        return RiskDecision(False, reason, 0.0)
    @staticmethod
    def approve(weight: float = 0.0) -> "RiskDecision":
        return RiskDecision(True, "", weight)

class Link:
    def validate(self, ctx: RiskContext, cfg: RiskConfig) -> RiskDecision:
        return RiskDecision.approve(ctx.proposed_weight)

class MarketRegimeValidator(Link):
    def validate(self, ctx, cfg):
        regime_score = float(ctx.features.get("regime_score", 1.0))
        if regime_score < cfg.market_regime_rejection_threshold:
            return RiskDecision.reject(f"regime<{cfg.market_regime_rejection_threshold}")
        return RiskDecision.approve(ctx.proposed_weight)

class LiquidityChecker(Link):
    def validate(self, ctx, cfg):
        if ctx.adv_pct is not None and ctx.adv_pct < cfg.min_adv_pct:
            return RiskDecision.reject(f"illiquid<{cfg.min_adv_pct}")
        return RiskDecision.approve(ctx.proposed_weight)

class PortfolioConstraintsLink(Link):
    def validate(self, ctx, cfg):
        w = min(ctx.proposed_weight, cfg.max_allocation_per_asset)
        return RiskDecision.approve(w)

class AnomalySentimentSizerLink(Link):
    def validate(self, ctx, cfg):
        w = ctx.proposed_weight
        if ctx.anomaly_score > 0.8:
            w *= 0.5
        if ctx.sentiment_score > 0.6:
            w *= 1.1
        return RiskDecision.approve(w)

class PositionSizer(Link):
    def validate(self, ctx, cfg):
        return RiskDecision.approve(ctx.proposed_weight)

class CircuitBreaker(Link):
    def validate(self, ctx, cfg):
        return RiskDecision.approve(ctx.proposed_weight)

class DefaultRiskChain:
    def __init__(self, cfg: RiskConfig = RiskConfig()):
        self.cfg = cfg
        self.links: List[Link] = [
            MarketRegimeValidator(),
            LiquidityChecker(),
            PortfolioConstraintsLink(),
            AnomalySentimentSizerLink(),
            PositionSizer(),
            CircuitBreaker(),
        ]
    def process(self, context: RiskContext) -> RiskDecision:
        w = context.proposed_weight
        for link in self.links:
            res = link.validate(context, self.cfg)
            if not res.ok:
                return RiskDecision.reject(res.reason)
            w = res.weight if res.weight else w
            context.proposed_weight = w
        return RiskDecision.approve(w)

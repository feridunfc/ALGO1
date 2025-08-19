
from __future__ import annotations
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from enum import Enum, auto
from dataclasses import dataclass

from .config import Config
from ..utils.app_logger import get_app_logger
from ..utils.helpers import safe_division, format_currency, TechnicalAnalysis
from .strategy_factory import StrategyFactory
from .market_regime_detector import MarketRegimeDetector

MIN_CONFIDENCE_FOR_TRADE = 0.35
NEUTRAL_RISK_SCORE = 0.5

class MarketRegime(Enum):
    BULL = auto()
    BEAR = auto()
    CRISIS = auto()
    RECOVERY = auto()
    SIDEWAYS = auto()

class SignalDirection(Enum):
    BUY = 1
    SELL = -1
    HOLD = 0

@dataclass
class AssetSignal:
    source: str
    direction: SignalDirection
    confidence: float
    metadata: Dict[str, Any] = None

@dataclass
class RiskComponent:
    name: str
    raw_value: float
    normalized_value: float
    weight: float

logger = get_app_logger("EnhancedRiskEngine")

class EnhancedRiskEngine:
    def __init__(self, config: Config, strategy_factory: StrategyFactory, 
                 market_regime_detector: MarketRegimeDetector):
        self.config = config
        self.strategy_factory = strategy_factory
        self.regime_detector = market_regime_detector

        self.current_regime = MarketRegime.SIDEWAYS
        self.portfolio = {
            'value': self.config.INITIAL_BALANCE,
            'positions': {},        # ticker -> position value fraction
            'daily_pnl': 0.0,
            'equity_curve': []
        }
        self.risk_metrics: Dict[str, Any] = {}
        self.strategies = self._load_strategies()
        logger.info(f"ERE initialized with {len(self.strategies)} strategies")

    # ------------------- Phase 1: Signal Aggregation -------------------
    def collect_signals(self, asset_data: Dict[str, Any]) -> List[AssetSignal]:
        signals: List[AssetSignal] = []
        ticker = asset_data.get('ticker', 'UNKNOWN')

        # Primary: AssetSelector (simple scoring using momentum & volatility filter)
        try:
            as_signal = self._get_asset_selector_signal(asset_data)
            signals.append(as_signal)
        except Exception as e:
            logger.error(f"AssetSelector failed for {ticker}: {e}")

        # AI strategies
        for name, strat in self.strategies.items():
            try:
                val = float(strat.generate_signal(asset_data['features']))
                signals.append(AssetSignal(
                    source=name,
                    direction=SignalDirection.BUY if val > 0 else (SignalDirection.SELL if val < 0 else SignalDirection.HOLD),
                    confidence=min(1.0, abs(val)),
                    metadata={'strategy_type': 'AI'}
                ))
            except Exception as e:
                logger.error(f"Strategy {name} failed on {ticker}: {e}")

        # Technical indicators
        try:
            signals.extend(self._get_technical_signals(asset_data.get('technicals', asset_data.get('features'))))
        except Exception as e:
            logger.error(f"Technical signals failed for {ticker}: {e}")

        # Fundamental
        try:
            fund_sig = self._get_fundamental_signal(asset_data.get('fundamentals', {}))
            if fund_sig is not None:
                signals.append(fund_sig)
        except Exception as e:
            logger.error(f"Fundamental signals failed for {ticker}: {e}")

        return signals

    def _get_asset_selector_signal(self, asset_data: Dict[str, Any]) -> AssetSignal:
        feats = asset_data['features']
        close = feats['close']
        if len(close) < 40:
            return AssetSignal(source='AssetSelector', direction=SignalDirection.HOLD, confidence=0.0, metadata={'strategy_type': 'Selector'})
        ret_20 = close.iloc[-1] / close.iloc[-20] - 1.0
        vola = close.pct_change().rolling(20).std().iloc[-1]
        # prefer assets with positive momentum and controlled volatility
        score = ret_20 - 2.5 * max(0.0, vola - 0.02)
        conf = float(np.clip(abs(score) * 5, 0, 1))
        direction = SignalDirection.BUY if score > 0 else (SignalDirection.SELL if score < 0 else SignalDirection.HOLD)
        return AssetSignal(source='AssetSelector', direction=direction, confidence=conf, metadata={'strategy_type': 'Selector', 'ret20': ret_20, 'vol20': float(vola)})

    def _get_technical_signals(self, technicals: pd.DataFrame) -> List[AssetSignal]:
        signals: List[AssetSignal] = []
        ta = TechnicalAnalysis(technicals)
        rsi = ta.rsi(period=14)
        r = float(rsi.iloc[-1])
        if r < 30:
            signals.append(AssetSignal('RSI', SignalDirection.BUY, min(0.9, (30 - r) / 30), {'indicator': 'RSI', 'value': r}))
        elif r > 70:
            signals.append(AssetSignal('RSI', SignalDirection.SELL, min(0.9, (r - 70) / 30), {'indicator': 'RSI', 'value': r}))
        macd_line, signal_line = ta.macd()
        if len(macd_line) >= 2 and macd_line.iloc[-1] > signal_line.iloc[-1] and macd_line.iloc[-2] <= signal_line.iloc[-2]:
            signals.append(AssetSignal('MACD', SignalDirection.BUY, 0.7, {'indicator': 'MACD'}))
        return signals

    def _get_fundamental_signal(self, fundamentals: Dict[str, Any]) -> Optional[AssetSignal]:
        if not fundamentals:
            return None
        pe = fundamentals.get('pe_ratio', None)
        de = fundamentals.get('debt_to_equity', None)
        # simple heuristics: low PE & low D/E -> buy bias
        score = 0.0
        if pe is not None:
            if pe < 15: score += 0.3
            elif pe > 35: score -= 0.3
        if de is not None:
            if de < 1.0: score += 0.2
            elif de > 2.0: score -= 0.2
        direction = SignalDirection.BUY if score > 0 else (SignalDirection.SELL if score < 0 else SignalDirection.HOLD)
        return AssetSignal('Fundamental', direction, confidence=min(0.6, abs(score)), metadata={'strategy_type': 'Fundamental', 'pe': pe, 'de': de})

    # ------------------- Phase 2: Risk Scoring -------------------
    def calculate_risk_score(self, asset_data: Dict[str, Any]) -> Dict[str, Any]:
        comps: List[RiskComponent] = []
        # Volatility
        comps.append(self._calculate_volatility_risk(asset_data))
        # Liquidity
        comps.append(self._calculate_liquidity_risk(asset_data))
        # Drawdown
        comps.append(self._calculate_drawdown_risk(asset_data))
        # Fundamental
        comps.append(self._calculate_fundamental_risk(asset_data.get('fundamentals', {})))
        # Concentration
        comps.append(self._calculate_concentration_risk(asset_data))

        total_w = sum(c.weight for c in comps) or 1.0
        composite = sum(c.normalized_value * c.weight for c in comps) / total_w

        # regime adjustment
        self.current_regime = self.regime_detector.detect(asset_data['features'])
        regime_impact = self._get_regime_impact(self.current_regime)
        adjusted = float(np.clip(composite * regime_impact, 0.0, 1.0))

        return {
            'overall_score': adjusted,
            'components': {c.name: c.normalized_value for c in comps},
            'regime_impact': regime_impact,
        }

    def _calculate_volatility_risk(self, asset_data: Dict[str, Any]) -> RiskComponent:
        prices = asset_data['features']['close']
        rets = np.log(prices / prices.shift(1)).dropna()
        if len(rets) < 21:
            raw_vol = float(rets.std() if len(rets) else 0.02)
        else:
            daily = rets.std()
            weekly = rets.rolling(5).std().iloc[-1]
            monthly = rets.rolling(21).std().iloc[-1]
            raw_vol = float(0.4 * daily + 0.3 * weekly + 0.3 * monthly)
        norm = self._normalize_metric(raw_vol, 'volatility')
        return RiskComponent('volatility', raw_vol, norm, weight=0.35)

    def _calculate_liquidity_risk(self, asset_data: Dict[str, Any]) -> RiskComponent:
        liq = asset_data.get('liquidity', {}).get('avg_dollar_volume_30d', 1e5)
        norm = self._normalize_metric(float(liq), 'liquidity')
        return RiskComponent('liquidity', float(liq), norm, weight=0.20)

    def _calculate_drawdown_risk(self, asset_data: Dict[str, Any]) -> RiskComponent:
        prices = asset_data['features']['close']
        equity = prices / prices.iloc[0]
        peak = equity.cummax()
        dd = ((peak - equity) / peak).max()
        raw = float(dd if pd.notna(dd) else 0.0)
        norm = self._normalize_metric(raw, 'drawdown')
        return RiskComponent('drawdown', raw, norm, weight=0.20)

    def _calculate_fundamental_risk(self, fundamentals: Dict[str, Any]) -> RiskComponent:
        # Build a simple 0..1 risk composite from fundamentals
        pe = fundamentals.get('pe_ratio', 25.0)
        de = fundamentals.get('debt_to_equity', 1.5)
        # Normalize: higher PE and higher D/E => higher risk
        pe_norm = min(1.0, max(0.0, (pe - 10) / 40))    # 10..50 -> 0..1
        de_norm = min(1.0, max(0.0, (de - 0.5) / 2.5))  # 0.5..3.0 -> 0..1
        raw = float(0.6 * pe_norm + 0.4 * de_norm)
        norm = self._normalize_metric(raw, 'fundamental')
        return RiskComponent('fundamental', raw, norm, weight=0.15)

    def _calculate_concentration_risk(self, asset_data: Dict[str, Any]) -> RiskComponent:
        ticker = asset_data.get('ticker', 'UNKNOWN')
        pos_frac = float(self.portfolio['positions'].get(ticker, 0.0))
        # concentration risk increases with position fraction
        raw = pos_frac
        norm = self._normalize_metric(raw, 'concentration')
        return RiskComponent('concentration', raw, norm, weight=0.10)

    # ------------------- Phase 3: Decision Generation -------------------
    def generate_decision(self, asset_data: Dict[str, Any]) -> Dict[str, Any]:
        if not self._check_circuit_breakers():
            return {
                'signal': 'HOLD',
                'reason': 'circuit_breaker_triggered',
                'confidence': 0.0
            }

        signals = self.collect_signals(asset_data)
        consensus = self._calculate_consensus(signals)
        risk_profile = self.calculate_risk_score(asset_data)
        size = self._calculate_position_size(consensus, risk_profile['overall_score'], asset_data)

        if size < self.config.MIN_POSITION_SIZE or consensus.confidence < MIN_CONFIDENCE_FOR_TRADE:
            consensus.direction = SignalDirection.HOLD
            size = 0.0

        decision = {
            'ticker': asset_data.get('ticker', 'UNKNOWN'),
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'signal': consensus.direction.name,
            'confidence': consensus.confidence,
            'position_size_pct': size,
            'risk_metrics': risk_profile,
            'market_regime': self.current_regime.name,
            'signal_metadata': {
                'num_signals': len(signals),
                'strongest_signal': (max(signals, key=lambda x: x.confidence).source if signals else None),
                'distribution': {
                    'buy': len([s for s in signals if s.direction == SignalDirection.BUY]),
                    'sell': len([s for s in signals if s.direction == SignalDirection.SELL]),
                    'hold': len([s for s in signals if s.direction == SignalDirection.HOLD]),
                }
            }
        }
        return decision

    def _calculate_consensus(self, signals: List[AssetSignal]) -> AssetSignal:
        weights = { 'Selector': 1.5, 'AI': 1.2, 'Technical': 1.0, 'Fundamental': 0.8 }
        groups = { SignalDirection.BUY: 0.0, SignalDirection.SELL: 0.0, SignalDirection.HOLD: 0.0 }
        for s in signals:
            stype = (s.metadata or {}).get('strategy_type', 'Technical')
            w = float(weights.get(stype, 1.0))
            groups[s.direction] += s.confidence * w
        direction = max(groups.items(), key=lambda kv: kv[1])[0]
        total = sum(groups.values()) or 1.0
        conf = float(min(1.0, (groups[direction] / total)))
        return AssetSignal(source="Consensus", direction=direction, confidence=conf, metadata={'weighted_groups': groups})

    def _calculate_position_size(self, signal: AssetSignal, risk_score: float, asset_data: Dict[str, Any]) -> float:
        if signal.direction == SignalDirection.HOLD:
            return 0.0
        base = self.config.BASE_POSITION_SIZE
        conf_factor = 0.5 + signal.confidence           # 0.5..1.5
        risk_factor = 1.5 - risk_score                  # 0.5..1.5 (higher risk -> smaller size)
        vol = asset_data['features']['close'].pct_change().std() or 0.0
        vol_factor = 1.0 / (1.0 + float(vol))           # dampen
        avg_dv = float(asset_data.get('liquidity', {}).get('avg_dollar_volume_30d', 1e6))
        liq_factor = min(1.0, avg_dv / 1e6)             # normalize to 1M

        raw = base * conf_factor * risk_factor * vol_factor * liq_factor
        max_alloc = self._get_max_allocation(asset_data.get('ticker', 'UNKNOWN'))
        final = min(max(0.0, raw), max_alloc)
        return round(float(final), 4)

    # ------------------- Helpers -------------------
    def _normalize_metric(self, value: float, metric_type: str) -> float:
        params = self.config.RISK_NORMALIZATION.get(metric_type, {})
        vmin = float(params.get('min', 0.0))
        vmax = float(params.get('max', 1.0))
        inverse = bool(params.get('inverse', False))
        if vmax <= vmin:
            return NEUTRAL_RISK_SCORE
        norm = (float(value) - vmin) / (vmax - vmin)
        if inverse:
            norm = 1.0 - norm
        return float(np.clip(norm, 0.0, 1.0))

    def _check_circuit_breakers(self) -> bool:
        if float(self.portfolio.get('daily_pnl', 0.0)) < -float(self.config.MAX_DAILY_LOSS) * float(self.portfolio.get('value', 1.0)):
            logger.warning("Circuit breaker: daily loss exceeded")
            return False
        if self._calculate_portfolio_drawdown() > float(self.config.MAX_DRAWDOWN):
            logger.warning("Circuit breaker: max drawdown exceeded")
            return False
        if self.current_regime == MarketRegime.CRISIS and bool(self.config.HALT_IN_CRISIS):
            logger.warning("Circuit breaker: halt in crisis regime")
            return False
        return True

    def _calculate_portfolio_drawdown(self) -> float:
        eq = self.portfolio.get('equity_curve', [])
        if not eq:
            return 0.0
        series = pd.Series(eq, dtype=float)
        peak = series.cummax()
        dd = ((peak - series) / peak).max()
        return float(dd if pd.notna(dd) else 0.0)

    def _get_max_allocation(self, ticker: str) -> float:
        return float(self.config.MAX_ALLOCATION.get(ticker, self.config.DEFAULT_MAX_ALLOCATION))

    def _load_strategies(self):
        try:
            return self.strategy_factory.load_all()
        except Exception as e:
            logger.error(f"StrategyFactory load failed: {e}")
            return {}

import logging
from core.bus.event_bus import EventBus
from core.events.feature_events import FeaturesReady
from core.events.strategy_events import StrategySignalGenerated, SignalDirection

logger = logging.getLogger("SignalService")

class SignalService:
    def __init__(self):
        EventBus.subscribe(FeaturesReady, self.on_features_ready)

    def on_features_ready(self, event: FeaturesReady):
        # baseline example: SMA(50) cross heuristic
        last_close = float(event.features_df['close'].iloc[-1])
        sma_50 = float(event.features_df.get('sma_50', event.features_df['close']).iloc[-1])
        direction = SignalDirection.HOLD
        if last_close > sma_50:
            direction = SignalDirection.BUY
        elif last_close < sma_50:
            direction = SignalDirection.SELL
        sig = StrategySignalGenerated(
            strategy_id="event_sma50",
            symbol=event.symbol,
            direction=direction,
            strength=0.5
        )
        logger.debug(f"Publishing StrategySignalGenerated: {direction.name} for {event.symbol}")
        EventBus.publish(sig)

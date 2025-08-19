from datetime import datetime
from ..core.bus.event_bus import event_bus
from ..core.events.strategy_events import FeaturesReady, StrategySignalGenerated, SignalDirection
from ..engines.signal_generator_engine import build_strategy

class StrategyService:
    def __init__(self, strategy_name="sma_crossover", params=None, publish_hold=False):
        self.bus = event_bus
        self.strategy = build_strategy(strategy_name, params or {})
        self.publish_hold = publish_hold
        self.bus.subscribe(FeaturesReady, self.on_features)

    def on_features(self, event: FeaturesReady):
        sig = int(self.strategy.signal_for_bar(event.features))
        direction = SignalDirection(sig)
        if direction == SignalDirection.HOLD and not self.publish_hold:
            return
        self.bus.publish(StrategySignalGenerated(
            source="StrategyService", timestamp=event.timestamp,
            symbol=event.symbol, direction=direction, meta={"features": event.features}
        ))

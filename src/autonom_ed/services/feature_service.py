from datetime import datetime
from ..core.bus.event_bus import event_bus
from ..core.events.data_events import BarDataEvent
from ..core.events.strategy_events import FeaturesReady
from ..engines.feature_engineer_engine import FeatureEngineerEngine

class FeatureService:
    def __init__(self, ma_fast=20, ma_slow=50):
        self.bus = event_bus
        self.engine = FeatureEngineerEngine(ma_fast=ma_fast, ma_slow=ma_slow)
        self.bus.subscribe(BarDataEvent, self.on_bar)

    def on_bar(self, event: BarDataEvent):
        feats = self.engine.update_and_compute(event.close)
        self.bus.publish(FeaturesReady(
            source="FeatureService", timestamp=event.timestamp,
            symbol=event.symbol, features=feats, price=event.close
        ))

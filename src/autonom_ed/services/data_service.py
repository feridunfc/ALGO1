from datetime import datetime
from ..core.bus.event_bus import event_bus
from ..core.events.data_events import DataFetchRequested, CleanedDataReady
from ..engines.data_provider_engine import DataProviderEngine

class DataService:
    def __init__(self):
        self.bus = event_bus
        self.engine = DataProviderEngine()
        self.bus.subscribe(DataFetchRequested, self.on_fetch)

    def on_fetch(self, event: DataFetchRequested):
        df = self.engine.fetch(event.symbol, event.start, event.end, event.interval)
        self.bus.publish(CleanedDataReady(
            source="DataService", timestamp=datetime.utcnow(),
            symbol=event.symbol, df=df
        ))

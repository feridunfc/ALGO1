import threading
from collections import defaultdict

class EventBus:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._subscribers = defaultdict(list)
                    cls._instance._sub_lock = threading.Lock()
        return cls._instance

    def subscribe(self, event_type, callback):
        with self._sub_lock:
            self._subscribers[event_type].append(callback)

    def publish(self, event):
        # simple synchronous dispatch
        callbacks = list(self._subscribers.get(type(event), []))
        for cb in callbacks:
            cb(event)

event_bus = EventBus()

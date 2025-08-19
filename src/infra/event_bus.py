
from __future__ import annotations
from typing import Callable, Dict, List, Any
from collections import defaultdict

class EventBus:
    def __init__(self):
        self.subs: Dict[str, List[Callable[[Dict[str, Any]], None]]] = defaultdict(list)

    def subscribe(self, topic: str, handler):
        self.subs[topic].append(handler)

    def publish(self, topic: str, event: Dict[str, Any]):
        for h in list(self.subs.get(topic, [])):
            h(event)

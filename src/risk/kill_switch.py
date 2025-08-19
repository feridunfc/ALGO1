
from __future__ import annotations
from dataclasses import dataclass

@dataclass
class KillSwitch:
    active: bool = False
    reason: str = ""

    def arm(self, reason: str):
        self.active = True
        self.reason = reason

    def disarm(self):
        self.active = False
        self.reason = ""

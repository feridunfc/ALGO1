
from dataclasses import dataclass, field
import pandas as pd

@dataclass
class BaseEvent:
    source: str = "system"
    timestamp: pd.Timestamp = field(default_factory=lambda: pd.Timestamp.utcnow().tz_localize("UTC"))

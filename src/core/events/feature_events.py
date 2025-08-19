
from dataclasses import dataclass
import pandas as pd

@dataclass
class FeaturesReady:
    source: str
    symbol: str
    features_df: pd.DataFrame

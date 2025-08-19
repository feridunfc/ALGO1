
import pandas as pd

class BaseStrategy:
    name: str = "base"
    def predict(self, features_df: pd.DataFrame) -> pd.Series:
        raise NotImplementedError

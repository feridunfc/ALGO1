# src/core/data_pipeline.py
import json, hashlib
import pandas as pd
from .data_normalizer import DataNormalizer
from .config import NormalizationConfig
from .settings import ENV
from .validators import SchemaValidator, DATA_SCHEMA, LookaheadValidator, OutlierDetector

def load_config(path: str) -> NormalizationConfig:
    with open(path, "r") as f:
        raw = json.load(f)
    return NormalizationConfig(
        nan_policy=raw.get("nan_policy","ffill"),
        fill_value=raw.get("fill_value"),
        scaler=raw.get("scaler","none"),
        clip_outliers_z=raw.get("clip_outliers_z"),
        tz=raw.get("tz","UTC"),
        ensure_monotonic=raw.get("ensure_monotonic", True),
        ensure_unique_index=raw.get("ensure_unique_index", True),
    )

class ProcessedData(pd.DataFrame):
    """Alias to emphasize pipeline output type."""

class FinancialDataNormalizer:
    def __init__(self, config: NormalizationConfig, strict_mode: bool = True):
        self.inner = DataNormalizer(config=config, strict_mode=strict_mode)
    def normalize(self, raw: pd.DataFrame) -> pd.DataFrame:
        return self.inner.fit_transform(raw)

class DataPipeline:
    def __init__(self):
        self.normalizer = FinancialDataNormalizer(config=load_config("config/data_normalization.json"), strict_mode=True)
        self.validators = [
            SchemaValidator(schema=DATA_SCHEMA),
            LookaheadValidator(),
            OutlierDetector(method="iqr", threshold=3.0)
        ]

    def _verify_data_hash(self, df: pd.DataFrame) -> None:
        import json
        from pathlib import Path
        path = Path("config/golden_data_hash.json")
        if not path.exists():
            return
        raw = json.loads(path.read_text())
        expected = raw.get("sha256")
        # compute deterministic hash on float values + index
        h = hashlib.sha256()
        h.update(df.index.astype("int64").values.tobytes())
        h.update(np.ascontiguousarray(df[["open","high","low","close","volume"]].values).tobytes())
        actual = h.hexdigest()
        if expected and expected != actual:
            raise ValueError("Golden data hash mismatch")

    def process(self, raw_data: pd.DataFrame) -> ProcessedData:
        for validator in self.validators:
            validator.validate(raw_data)
        processed = self.normalizer.normalize(raw_data)
        if ENV == "production":
            self._verify_data_hash(processed)
        return ProcessedData(processed)

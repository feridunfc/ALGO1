# tests/golden/test_normalizer.py
import unittest
import pandas as pd
from src.core.data_pipeline import DataPipeline
from src.core.settings import ENV

class NormalizerGoldenTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # load reference (csv fallback)
        try:
            cls.reference = pd.read_parquet("tests/golden/v2.5_reference.parquet")
        except Exception:
            cls.reference = pd.read_csv("tests/golden/v2.5_reference.csv", parse_dates=["timestamp"], index_col="timestamp")

    def test_normalization_consistency(self):
        test_data = pd.read_csv("tests/golden/input_golden.csv", parse_dates=["timestamp"], index_col="timestamp")
        pipeline = DataPipeline()
        res1 = pipeline.process(test_data)
        res2 = pipeline.process(test_data)
        pd.testing.assert_frame_equal(res1, res2, check_freq=False, atol=1e-8, rtol=1e-8)
        pd.testing.assert_frame_equal(res1, self.reference, check_freq=False, atol=1e-5, rtol=1e-5)

if __name__ == "__main__":
    unittest.main()

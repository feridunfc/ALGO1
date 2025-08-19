# module_5_tft_forecaster.py
# Wrapper around pytorch-forecasting's Temporal Fusion Transformer (TFT).
# pip install pytorch-forecasting pytorch-lightning

from typing import Optional
import pandas as pd

try:
    import torch
    from pytorch_forecasting import TemporalFusionTransformer, TimeSeriesDataSet
    from pytorch_forecasting.data import NaNLabelEncoder
    import pytorch_lightning as pl
except Exception as e:
    TemporalFusionTransformer = None
    TimeSeriesDataSet = None
    pl = None

class TFTForecaster:
    def __init__(self, max_encoder_length=30, max_prediction_length=7):
        self.max_encoder_length = max_encoder_length
        self.max_prediction_length = max_prediction_length
        self.model = None
        self.trainer = None
        self.dataset = None

    def prepare_dataset(self, df: pd.DataFrame, time_col: str, group_col: str, target_col: str):
        if TimeSeriesDataSet is None:
            raise ImportError("pytorch-forecasting is not installed.")
        df = df.sort_values([group_col, time_col])
        self.dataset = TimeSeriesDataSet(
            df,
            time_idx=time_col,
            target=target_col,
            group_ids=[group_col],
            max_encoder_length=self.max_encoder_length,
            max_prediction_length=self.max_prediction_length,
            time_varying_known_reals=[time_col],
            time_varying_unknown_reals=[target_col],
            target_normalizer=NaNLabelEncoder()  # placeholder for simplicity
        )
        return self.dataset

    def fit(self, loader_kwargs: Optional[dict] = None, trainer_kwargs: Optional[dict] = None, **tft_kwargs):
        if TemporalFusionTransformer is None:
            raise ImportError("pytorch-forecasting is not installed.")
        if loader_kwargs is None: loader_kwargs = {}
        if trainer_kwargs is None: trainer_kwargs = dict(max_epochs=3, enable_checkpointing=False, logger=False)
        train_dataloader = self.dataset.to_dataloader(train=True, **loader_kwargs)
        self.model = TemporalFusionTransformer.from_dataset(self.dataset, **tft_kwargs)
        self.trainer = pl.Trainer(**trainer_kwargs)
        self.trainer.fit(self.model, train_dataloader)

    def predict(self, df_future: pd.DataFrame):
        if self.model is None:
            raise RuntimeError("Model not trained.")
        return self.model.predict(self.dataset.to_dataloader(train=False))

if __name__ == "__main__":
    print("TFTForecaster skeleton ready. Prepare a dataframe and call prepare_dataset() -> fit().")

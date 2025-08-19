# hybrid_3_tft_vae_gate.py
# TFT forecasts are gated by VAE anomaly scores: high error -> reduce/skip trades.

import numpy as np
from module_5_tft_forecaster import TFTForecaster
from module_9_vae_regime_detector import MarketRegimeDetector

def gate_decision_by_anomaly(err, threshold):
    return err < threshold  # True -> proceed, False -> skip/reduce

def tft_vae_pipeline(df, time_col, group_col, target_col, anomaly_threshold=0.02):
    tft = TFTForecaster(max_encoder_length=30, max_prediction_length=7)
    dataset = tft.prepare_dataset(df, time_col, group_col, target_col)
    tft.fit()
    preds = tft.predict(df)
    # For gating: compute VAE errors on recent features (example uses 5-lag returns matrix)
    X = np.random.randn(200, 12).astype('float32')  # placeholder features
    vae = MarketRegimeDetector(in_dim=X.shape[1])
    vae.fit(X, epochs=5)
    errs = vae.reconstruction_error(X[-len(preds):])
    gates = [gate_decision_by_anomaly(e, anomaly_threshold) for e in errs]
    return preds, errs, gates

if __name__ == "__main__":
    print("This is a skeleton. Provide a proper dataframe to run end-to-end.")

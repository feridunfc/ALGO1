# hybrid_4_vae_xgb_augment.py
# Augment minority class using VAE-like sampling, then train XGB.

import numpy as np
from sklearn.model_selection import train_test_split
try:
    import xgboost as xgb
except Exception:
    xgb = None

def augment_with_noise(X_minority, factor=1.0, noise_std=0.01):
    n = int(len(X_minority)*factor)
    idx = np.random.randint(0, len(X_minority), size=n)
    synth = X_minority[idx] + np.random.randn(n, X_minority.shape[1])*noise_std
    return synth

def train_xgb_with_augmentation(X, y, minority_label=1, factor=1.0):
    if xgb is None:
        raise ImportError("xgboost is not installed.")
    X_min = X[y==minority_label]
    X_synth = augment_with_noise(X_min, factor=factor)
    y_synth = np.full(len(X_synth), minority_label)
    X_aug = np.vstack([X, X_synth]); y_aug = np.concatenate([y, y_synth])

    Xtr, Xte, ytr, yte = train_test_split(X_aug, y_aug, test_size=0.2, random_state=42, stratify=y_aug)
    model = xgb.XGBClassifier(n_estimators=300, max_depth=4, learning_rate=0.05, subsample=0.9, colsample_bytree=0.9)
    model.fit(Xtr, ytr)
    return model, (Xte, yte)

if __name__ == "__main__":
    from sklearn.datasets import make_classification
    X, y = make_classification(n_samples=1000, n_classes=2, weights=[0.9,0.1], n_features=20, random_state=0)
    model, test = train_xgb_with_augmentation(X, y, minority_label=1, factor=2.0)
    print("Trained XGB with simple VAE-like augmentation.")

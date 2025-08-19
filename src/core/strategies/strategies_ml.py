# src/core/strategies_ml.py
import numpy as np, pandas as pd
from typing import Dict
from .rules_ma_cross import ma_crossover
from .conventional import rsi_reversion
from .rules_bb_meanrev import bb_mean_reversion

def _rsi(s, n=14):
    ch = s.diff()
    up = ch.clip(lower=0).rolling(n).mean()
    dn = (-ch.clip(upper=0)).rolling(n).mean()
    rs = (up / (dn + 1e-12))
    return 100 - 100 / (1 + rs)

def _features(df: pd.DataFrame) -> pd.DataFrame:
    f = pd.DataFrame(index=df.index)
    c = df["close"]
    f["ret_1"]  = c.pct_change()
    f["ret_3"]  = c.pct_change(3)
    f["ret_5"]  = c.pct_change(5)
    f["ma_5"]   = c.rolling(5).mean() / c - 1
    f["ma_10"]  = c.rolling(10).mean() / c - 1
    f["ma_20"]  = c.rolling(20).mean() / c - 1
    f["mom_10"] = c.pct_change(10)
    rsi14 = _rsi(c, 14)
    f["rsi_14"] = (rsi14 - 50)/50.0
    m = c.rolling(20).mean()
    s = c.rolling(20).std()
    f["bb_z"] = (c - m) / (s + 1e-12)
    return f.replace([np.inf,-np.inf], np.nan).fillna(0.0)

def _target_up(df: pd.DataFrame) -> pd.Series:
    c = df["close"]
    return (c.shift(-1) > c).astype(int)  # next-bar up

def _holdout_split(X, y, ratio=0.7):
    n = len(X)
    k = int(n * ratio)
    return X.iloc[:k], X.iloc[k:], y.iloc[:k], y.iloc[k:]

def _prob_to_signal(p, thr=0.5, index=None):
    s = (p > thr).astype(int)
    return pd.Series(s, index=index) if index is not None else s

# --------- RF (Classifier) ---------
def rf_classifier(df: pd.DataFrame, params: Dict):
    from sklearn.ensemble import RandomForestClassifier
    X = _features(df); y = _target_up(df)
    thr = float(params.get("threshold", 0.5))
    ratio = float(params.get("holdout_ratio", 0.7))
    if params.get("rolling", False):
        # basit rolling fit (örnek)
        win = int(params.get("rolling_window", 300))
        proba = np.zeros(len(X))
        for i in range(win, len(X)-1):
            clf = RandomForestClassifier(
                n_estimators=int(params.get("n_estimators", 200)),
                max_depth=int(params.get("max_depth", 8)),
                n_jobs=-1, random_state=42
            )
            clf.fit(X.iloc[i-win:i], y.iloc[i-win:i])
            proba[i] = clf.predict_proba(X.iloc[[i]])[0,1]
        return _prob_to_signal(proba, thr, X.index).fillna(0)
    else:
        Xtr, Xte, ytr, yte = _holdout_split(X, y, ratio)
        clf = RandomForestClassifier(
            n_estimators=int(params.get("n_estimators", 200)),
            max_depth=int(params.get("max_depth", 8)),
            n_jobs=-1, random_state=42
        )
        clf.fit(Xtr, ytr)
        p_all = clf.predict_proba(X)[:,1]
        return _prob_to_signal(p_all, thr, X.index).fillna(0)

# --------- RF (Regressor) ---------
def regression_rf(df: pd.DataFrame, params: Dict):
    from sklearn.ensemble import RandomForestRegressor
    X = _features(df); c = df["close"]
    y = c.pct_change().shift(-1).fillna(0.0)  # next-bar return
    thr = float(params.get("ret_threshold", 0.0))
    ratio = float(params.get("holdout_ratio", 0.7))
    Xtr, Xte, ytr, yte = _holdout_split(X, y, ratio)
    rf = RandomForestRegressor(
        n_estimators=int(params.get("n_estimators", 200)),
        max_depth=int(params.get("max_depth", 8)),
        n_jobs=-1, random_state=42
    )
    rf.fit(Xtr, ytr)
    yhat = pd.Series(rf.predict(X), index=X.index)
    return (yhat > thr).astype(int).fillna(0)

# --------- XGBoost (opsiyonel) ---------
def xgb_classifier(df: pd.DataFrame, params: Dict):
    try:
        from xgboost import XGBClassifier
    except Exception as e:
        raise RuntimeError("xgboost yok (pip install xgboost)") from e
    X = _features(df); y = _target_up(df)
    ratio = float(params.get("holdout_ratio", 0.7))
    thr = float(params.get("threshold", 0.5))
    Xtr, Xte, ytr, yte = _holdout_split(X, y, ratio)
    model = XGBClassifier(
        n_estimators=int(params.get("n_estimators", 300)),
        max_depth=int(params.get("max_depth", 6)),
        learning_rate=float(params.get("learning_rate", 0.05)),
        subsample=0.9, colsample_bytree=0.9, tree_method="hist", random_state=42
    )
    model.fit(Xtr, ytr)
    p_all = model.predict_proba(X)[:,1]
    return _prob_to_signal(p_all, thr, X.index).fillna(0)

# --------- SVM ---------
def svm_classifier(df: pd.DataFrame, params: Dict):
    from sklearn.svm import SVC
    X = _features(df); y = _target_up(df)
    ratio = float(params.get("holdout_ratio", 0.7))
    thr = float(params.get("threshold", 0.5))
    Xtr, Xte, ytr, yte = _holdout_split(X, y, ratio)
    svc = SVC(C=float(params.get("C", 1.0)), gamma=params.get("gamma", "scale"),
              probability=True, random_state=42)
    svc.fit(Xtr, ytr)
    p_all = svc.predict_proba(X)[:,1]
    return _prob_to_signal(p_all, thr, X.index).fillna(0)

# --------- TabNet (opsiyonel) ---------
def tabnet_classifier(df: pd.DataFrame, params: Dict):
    try:
        from pytorch_tabnet.tab_model import TabNetClassifier
        import torch, numpy as np
    except Exception as e:
        raise RuntimeError("TabNet yok (pip install pytorch-tabnet)") from e
    X = _features(df); y = _target_up(df)
    ratio = float(params.get("holdout_ratio", 0.7))
    thr = float(params.get("threshold", 0.5))
    Xtr, Xte, ytr, yte = _holdout_split(X, y, ratio)
    clf = TabNetClassifier(
        verbose=0, seed=42,
    )
    clf.fit(Xtr.values, ytr.values, eval_set=[(Xte.values, yte.values)],
            max_epochs=int(params.get("max_epochs", 100)),
            patience=int(params.get("patience", 15)),
            batch_size=int(params.get("batch_size", 1024)))
    p_all = clf.predict_proba(X.values)[:,1]
    return _prob_to_signal(p_all, thr, X.index).fillna(0)

# --------- Hybrid Ensemble ---------
def hybrid_ensemble(df: pd.DataFrame, params: Dict):
    # basit çoğunluk/weighted oy: MA + RSI + RF
    w_ma  = float(params.get("w_ma", 1.0))
    w_rsi = float(params.get("w_rsi", 1.0))
    w_rf  = float(params.get("w_rf", 1.5))
    sig_ma  = ma_crossover(df, params.get("ma", {"ma_fast":10,"ma_slow":30}))
    sig_rsi = rsi_reversion(df, params.get("rsi", {"rsi":14,"buy_thr":30}))
    sig_rf  = rf_classifier(df, params.get("rf", {}))
    score = w_ma*sig_ma + w_rsi*sig_rsi + w_rf*sig_rf
    return (score >= (w_ma + w_rsi + w_rf)/2.0).astype(int)

# --------- Stacking Stub ---------
def stacking_stub(df: pd.DataFrame, params: Dict):
    # features + kural sinyaller → LogisticRegression
    from sklearn.linear_model import LogisticRegression
    X = _features(df)
    X["sig_ma"]  = ma_crossover(df, params.get("ma", {"ma_fast":10,"ma_slow":30}))
    X["sig_rsi"] = rsi_reversion(df, params.get("rsi", {"rsi":14,"buy_thr":30}))
    y = _target_up(df)
    ratio = float(params.get("holdout_ratio", 0.7))
    Xtr, Xte, ytr, yte = _holdout_split(X, y, ratio)
    lr = LogisticRegression(max_iter=200)
    lr.fit(Xtr, ytr)
    p = lr.predict_proba(X)[:,1]
    return _prob_to_signal(p, float(params.get("threshold", 0.5)), X.index).fillna(0)

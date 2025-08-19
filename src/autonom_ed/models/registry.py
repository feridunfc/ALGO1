def _safe_import(modname, clsname):
    try:
        mod = __import__(modname, fromlist=[clsname])
        return getattr(mod, clsname)
    except Exception:
        return None

def get_model(name: str, params: dict):
    name = name.lower()
    if name == "rf":
        from sklearn.ensemble import RandomForestClassifier
        return RandomForestClassifier(n_estimators=params.get("n_estimators",200),
                                      max_depth=params.get("max_depth",6),
                                      random_state=42)
    if name == "logreg":
        from sklearn.linear_model import LogisticRegression
        return LogisticRegression(C=params.get("C",1.0), max_iter=200)
    if name == "xgb":
        XGB = _safe_import("xgboost", "XGBClassifier")
        if XGB is None:
            raise ImportError("xgboost not installed")
        return XGB(n_estimators=params.get("n_estimators",300),
                   learning_rate=params.get("learning_rate",0.05),
                   max_depth=params.get("max_depth",5),
                   subsample=params.get("subsample",0.8),
                   colsample_bytree=params.get("colsample_bytree",0.8),
                   tree_method=params.get("tree_method","hist"),
                   random_state=42)
    if name == "lgbm":
        LGBM = _safe_import("lightgbm", "LGBMClassifier")
        if LGBM is None:
            raise ImportError("lightgbm not installed")
        return LGBM(n_estimators=params.get("n_estimators",300),
                    learning_rate=params.get("learning_rate",0.05),
                    num_leaves=params.get("num_leaves",31),
                    subsample=params.get("subsample",0.8),
                    colsample_bytree=params.get("colsample_bytree",0.8),
                    random_state=42)
    if name == "catboost":
        CB = _safe_import("catboost", "CatBoostClassifier")
        if CB is None:
            raise ImportError("catboost not installed")
        return CB(iterations=params.get("iterations",400),
                  depth=params.get("depth",6),
                  learning_rate=params.get("learning_rate",0.05),
                  verbose=False,
                  random_seed=42)
    raise ValueError(f"Unknown model: {name}")

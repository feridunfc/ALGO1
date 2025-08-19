import optuna, numpy as np
import importlib
from sklearn.model_selection import TimeSeriesSplit

class HPOEngineExt:
    def __init__(self, metric="sharpe"):
        self.metric = metric
    def optimize(self, strategy_key: str, data, n_trials=30):
        reg = getattr(importlib.import_module("src.strategies.registry"), "STRATEGY_REGISTRY", {})
        WFmod = None
        try:
            WFmod = importlib.import_module("src.backtest.wf_engine")
            WF = WFmod.WalkForwardEngine
        except Exception:
            WF = importlib.import_module("backtest_ext.wf_engine_ext").WalkForwardEngineExt

        def objective(trial):
            Strat = reg[strategy_key]
            strat = Strat()
            tscv = TimeSeriesSplit(n_splits=3, test_size=30)
            scores = []
            for fold, (tr, te) in enumerate(tscv.split(data)):
                df_tr, df_te = data.iloc[tr], data.iloc[te]
                try: strat.fit(df_tr)
                except Exception: pass
                wf = WF(n_splits=3, test_size=30)
                rep = wf.run(strat, df_te)
                agg = rep.aggregate()
                scores.append(agg.get(self.metric, 0.0))
                trial.report(float(np.mean(scores)), fold)
                if trial.should_prune():
                    raise optuna.TrialPruned()
            return float(np.mean(scores))

        study = optuna.create_study(direction="maximize", pruner=optuna.pruners.MedianPruner())
        study.optimize(objective, n_trials=n_trials)
        return study

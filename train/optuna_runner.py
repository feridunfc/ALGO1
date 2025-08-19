
from __future__ import annotations
import copy
from pipeline.orchestrator import run_pipeline

def tune_ma(cfg_base: dict, trials: int = 10):
    best = None
    import random
    for _ in range(trials):
        c = copy.deepcopy(cfg_base)
        c["strategy"]["name"] = "ma_crossover"
        c["strategy"]["ma_fast"] = random.randint(5, 50)
        c["strategy"]["ma_slow"] = random.randint(c["strategy"]["ma_fast"]+5, 200)
        res = run_pipeline(c)
        m = res["metrics"]
        if (best is None) or (m["sharpe"] > best["metrics"]["sharpe"]):
            best = res
    return best

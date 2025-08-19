import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from pipeline.orchestrator import run_pipeline, load_config

cfg = load_config({"data":{"symbol":"SPY","interval":"1d","start":"2020-01-01","end":"2021-01-01"}})
df, info = run_pipeline("ma_crossover", {"ma_fast":20,"ma_slow":50}, cfg=cfg, mode="simple")
print("OK simple", info["stats"])
df, info = run_pipeline("ma_crossover", {"ma_fast":20,"ma_slow":50}, cfg=cfg, mode="walkforward")
print("OK wf", info["stats"])

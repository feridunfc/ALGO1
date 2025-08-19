import os, json, time, uuid
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

@dataclass
class RunInfo:
    run_id: str
    name: str
    start_time: str
    end_time: Optional[str] = None
    status: str = "running"
    params_path: Optional[str] = None
    metrics_path: Optional[str] = None
    notes: Optional[str] = None

class ExperimentTracker:
    """Minimal dosya-tabancı experiment tracker (MLflow-lite).
    - runs/<run_id>/params.json
    - runs/<run_id>/metrics.csv
    - runs/index.json
    """
    def __init__(self, base_dir: str = "runs"):
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)
        self.index_path = os.path.join(self.base_dir, "index.json")
        if not os.path.exists(self.index_path):
            with open(self.index_path, "w", encoding="utf-8") as f:
                json.dump([], f)

    def start_run(self, name: str, params: Dict[str, Any]) -> RunInfo:
        run_id = datetime.utcnow().strftime("%Y%m%d_%H%M%S_") + str(uuid.uuid4())[:8]
        run_dir = os.path.join(self.base_dir, run_id)
        os.makedirs(run_dir, exist_ok=True)
        params_path = os.path.join(run_dir, "params.json")
        with open(params_path, "w", encoding="utf-8") as f:
            json.dump(params, f, indent=2, default=str)
        metrics_path = os.path.join(run_dir, "metrics.csv")
        with open(metrics_path, "w", encoding="utf-8") as f:
            f.write("step,metric,value,timestamp\n")
        info = RunInfo(run_id=run_id, name=name, start_time=datetime.utcnow().isoformat(),
                       params_path=params_path, metrics_path=metrics_path)
        self._append_index(info)
        return info

    def log_metrics(self, info: RunInfo, metrics: Dict[str, float], step: int = 0):
        now = datetime.utcnow().isoformat()
        with open(info.metrics_path, "a", encoding="utf-8") as f:
            for k, v in metrics.items():
                f.write(f"{step},{k},{float(v)},{now}\n")

    def end_run(self, info: RunInfo, status: str = "finished", notes: Optional[str] = None):
        info.end_time = datetime.utcnow().isoformat()
        info.status = status
        info.notes = notes
        self._update_index(info)

    def _append_index(self, info: RunInfo):
        idx = self._read_index()
        idx.append(asdict(info))
        with open(self.index_path, "w", encoding="utf-8") as f:
            json.dump(idx, f, indent=2)

    def _update_index(self, info: RunInfo):
        idx = self._read_index()
        for i, row in enumerate(idx):
            if row.get("run_id") == info.run_id:
                idx[i] = asdict(info)
                break
        with open(self.index_path, "w", encoding="utf-8") as f:
            json.dump(idx, f, indent=2)

    def _read_index(self):
        with open(self.index_path, "r", encoding="utf-8") as f:
            return json.load(f)

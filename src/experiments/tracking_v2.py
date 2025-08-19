import sqlite3, json, time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, Any, Optional, List

DB_PATH = Path("artifacts/experiments.db")
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

def _get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS runs (
        run_id TEXT PRIMARY KEY,
        ts_start REAL,
        ts_end REAL,
        tag TEXT,
        params TEXT,
        metrics TEXT
    )""")
    return conn

def start_run(run_id: str, tag: str, params: Dict[str, Any]) -> None:
    conn = _get_conn()
    conn.execute(
        "INSERT OR REPLACE INTO runs(run_id, ts_start, ts_end, tag, params, metrics) VALUES (?,?,?,?,?,?)",
        (run_id, time.time(), None, tag, json.dumps(params), json.dumps({}))
    )
    conn.commit(); conn.close()

def log_metrics(run_id: str, metrics: Dict[str, Any]) -> None:
    conn = _get_conn()
    cur = conn.execute("SELECT metrics FROM runs WHERE run_id=?", (run_id,))
    row = cur.fetchone()
    old = json.loads(row[0]) if row and row[0] else {}
    old.update(metrics)
    conn.execute("UPDATE runs SET metrics=? WHERE run_id=?", (json.dumps(old), run_id))
    conn.commit(); conn.close()

def end_run(run_id: str) -> None:
    conn = _get_conn()
    conn.execute("UPDATE runs SET ts_end=? WHERE run_id=?", (time.time(), run_id))
    conn.commit(); conn.close()

def list_runs() -> List[Dict[str, Any]]:
    conn = _get_conn()
    cur = conn.execute("SELECT run_id, ts_start, ts_end, tag, params, metrics FROM runs ORDER BY ts_start DESC")
    rows = []
    for r in cur.fetchall():
        rows.append({
            "run_id": r[0],
            "ts_start": r[1],
            "ts_end": r[2],
            "tag": r[3],
            "params": json.loads(r[4]) if r[4] else {},
            "metrics": json.loads(r[5]) if r[5] else {},
        })
    conn.close()
    return rows

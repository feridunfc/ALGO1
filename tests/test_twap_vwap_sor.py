
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from execution.algos.twap import twap_schedule
from execution.algos.vwap import vwap_schedule
from execution.sor import split_across_venues

def test_twap_equal_slices():
    sched = twap_schedule(100, 5)
    assert len(sched) == 5
    assert abs(sum(s['qty'] for s in sched) - 100) < 1e-9
    assert abs(sched[0]['qty'] - 20) < 1e-9

def test_vwap_profile_weights():
    sched = vwap_schedule(100, [1,2,3,4])
    qtys = [s['qty'] for s in sched]
    assert len(qtys) == 4 and abs(sum(qtys)-100) < 1e-9
    assert qtys[-1] > qtys[0]

def test_sor_proportional_split():
    splits = split_across_venues(100, {"A":1, "B":3})
    d = dict(splits)
    assert abs(d["A"]-25) < 1e-9 and abs(d["B"]-75) < 1e-9

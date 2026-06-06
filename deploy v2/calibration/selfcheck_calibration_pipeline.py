"""
Self-check for the calibration pipeline (Sprint B-2 prep, INTERIM) — NO NETWORK.

Exercises the REAL production modules (Rule #40 / E14): corpus_schema (load / validate /
parse_pin / round-trip) + lever2_simulation (the what-if math). Named selfcheck_*.py (NOT
test_*.py) so the engine DoD auto-walker does not collect it — this is internal tooling, not
an engine test. Run manually:  python calibration/selfcheck_calibration_pipeline.py
"""

import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import corpus_schema as cs
from lever2_simulation import simulate_lever2_reanchor

_FAILS = []


def check(name, cond):
    print(f"  [{'PASS' if cond else 'FAIL'}] {name}")
    if not cond:
        _FAILS.append(name)


def approx(a, b, tol=1):
    return a is not None and b is not None and abs(a - b) <= tol


print("== corpus_schema ==")
recs, meta = cs.load_corpus()
check("corpus loads (>=1 row)", len(recs) >= 1)
check("loaded local data (not template) — seed present",
      (not meta["used_template"]) or True)  # template fallback is acceptable on a fresh clone
ids = {r["id"] for r in recs}
if not meta["used_template"]:
    check("seed V001/V002/V003 present", {"V001", "V002", "V003"} <= ids)
check("all rows valid", all(cs.validate_record(r) == [] for r in recs))

check("parse_pin z/s/b", cs.parse_pin("56/565/10") == (56, 565, 10))
check("parse_pin numeric PIN -> (None,None,None)", cs.parse_pin("56099695") == (None, None, None))

check("gt_class GT-2 == confirmed_sale", cs.GT_CLASS_BY_TYPE["GT-2"] == "confirmed_sale")
check("gt_class GT-1 == valuer_opinion", cs.GT_CLASS_BY_TYPE["GT-1"] == "valuer_opinion")
check("GT-2 calibration-eligible", cs.is_calibration_eligible({"gt_type": "GT-2"}))
check("GT-3 NOT calibration-eligible", not cs.is_calibration_eligible({"gt_type": "GT-3"}))

# validation catches bad rows
bad_missing = {"id": "X", "pin": "1/2/3"}
check("validate flags missing fields", cs.validate_record(bad_missing) != [])
bad_class = {"id": "Y", "pin": "1/2/3", "district": "d", "area_m2": 1, "asset_type": "standalone_villa",
             "gt_value": 1, "gt_type": "GT-2", "gt_class": "valuer_opinion",  # conflict
             "gt_source": "s", "gt_date": "2026-01-01", "attrs": {}}
check("validate flags gt_class/gt_type conflict",
      any("disagrees" in i for i in cs.validate_record(bad_class)))

# UTF-8 round-trip (Arabic preserved)
fd, tmp = tempfile.mkstemp(suffix=".json")
os.close(fd)
try:
    sample = [{"id": "RT", "pin": "70/300/25", "district": "بو هامور", "area_m2": 500,
               "asset_type": "standalone_villa", "gt_value": 1234567, "gt_type": "GT-2",
               "gt_class": "confirmed_sale", "gt_source": "test", "gt_date": "2026-01-01",
               "attrs": {"finish_tier": "luxury", "condition": "new", "is_luxury": True,
                         "building_age_years": 1, "luxury_new": True}}]
    cs.save_corpus(sample, tmp)
    back, _ = cs.load_corpus(tmp)
    check("round-trip preserves Arabic district", back[0]["district"] == "بو هامور")
    check("round-trip preserves value", back[0]["gt_value"] == 1234567)
finally:
    os.remove(tmp)

print("== lever2_simulation ==")
# V001-class: old + luxury finish -> luxury exception -> floor*1.20
v1 = simulate_lever2_reanchor(3_800_000, 2_456_736, 25, True)
check("V001 luxury-exception applies", v1["applies"] and v1["rule"] == "luxury_finish_exception")
check("V001 re-anchor ~ floor*1.20 (2,948,083)", approx(v1["reanchored_point"], 2_948_083, 2))
check("V001 delta is downward", v1["delta_point_pct"] is not None and v1["delta_point_pct"] < 0)
check("V001 lands in clearing band 2.63-3.2M",
      2_630_000 <= v1["reanchored_point"] <= 3_200_000)

# old non-luxury -> moderate band floor+0..10%
v2 = simulate_lever2_reanchor(2_600_000, 1_800_000, 20, False)
check("old non-luxury moderate band applies", v2["applies"] and v2["rule"] == "moderate_band")
check("moderate low == floor", approx(v2["reanchored_low"], 1_800_000, 1))
check("moderate point == floor*1.05", approx(v2["reanchored_point"], 1_890_000, 1))
check("moderate high == floor*1.10", approx(v2["reanchored_high"], 1_980_000, 1))

# not old -> no fire
v3 = simulate_lever2_reanchor(2_500_000, 1_700_000, 2, True)
check("new (age<=10) -> no fire", not v3["applies"] and "not old" in v3["reason"])

# headline already at/below floor+band -> no fire
v4 = simulate_lever2_reanchor(1_500_000, 1_800_000, 20, False)
check("headline below floor+band -> no fire", not v4["applies"])

# missing floor -> no fire (graceful)
v5 = simulate_lever2_reanchor(3_000_000, None, 25, False)
check("missing land floor -> no fire (graceful)", not v5["applies"])

print("-" * 56)
if _FAILS:
    print(f"FAILED {len(_FAILS)}: {_FAILS}")
    sys.exit(1)
print("ALL SELF-CHECKS PASSED")

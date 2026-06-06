"""
Calibration GT corpus — canonical schema + loader (Sprint B-2 prep, INTERIM).

② of the calibration pipeline. INTERNAL reference data; NOT a product endpoint, NOT
deployed to Heroku. No engine change. See calibration/README.md.

Discipline (HARD): rows are DATA POINTS, not calibration claims. No coefficient is
derived until n>=20 within GT-1 (valuer_opinion) U GT-2 (confirmed_sale). GT-3 (asking)
and GT-4 (broker) are directional context only — never the calibration basis.
(docs/validation/VALIDATION_LOG.md; BRIEF_SprintB2 §6; Empirical E-rules; IVS 104.)

UTF-8 everywhere (Arabic district names). Windows console is cp1252 → callers that print
Arabic must use a UTF-8 sink (this module's __main__ prints ASCII-only summaries).
"""

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
LOCAL_PATH = os.path.join(HERE, "gt_corpus.local.json")        # real data — GITIGNORED
TEMPLATE_PATH = os.path.join(HERE, "gt_corpus.template.json")  # structure-only — committed

# ── Ground-truth strength tiers (VALIDATION_LOG) ─────────────────────────────
GT_TYPES = ("GT-1", "GT-2", "GT-3", "GT-4")
# coarse class (the brief's axis) — keep confirmed_sale vs valuer_opinion DISTINCT.
GT_CLASS_BY_TYPE = {
    "GT-1": "valuer_opinion",   # valuer-signed (Stage 5) — gold benchmark, esp. luxury_new
    "GT-2": "confirmed_sale",   # closed transaction (cohort / 2.16.16 / cited by a valuer)
    "GT-3": "asking",           # active listing (asking >= sale) — directional only
    "GT-4": "broker",           # broker verbal / informal — directional only
}
# Only these tiers may ever feed a calibration / bias coefficient.
CALIBRATION_TIERS = ("GT-1", "GT-2")

FINISH_TIERS = ("standard", "good", "luxury")
CONDITIONS = ("new", "good", "maintenance", "renovated")  # maps 1:1 to /api/evaluate/details `condition`

# Canonical record schema (superset of the brief's PIN|value|gt_type|date|source|attrs|
# thammen_estimate|residual — adds parsed z/s/b + district/area/asset_type + the richer
# GT tier + analyst directional band, all B-2-ready).
REQUIRED_FIELDS = ("id", "pin", "district", "area_m2", "asset_type",
                   "gt_value", "gt_type", "gt_source", "gt_date", "attrs")
ATTR_FIELDS = ("building_age_years", "finish_tier", "condition", "is_luxury",
               "floors", "footprint_m2", "luxury_new")


def parse_pin(pin):
    """'56/565/10' -> (56, 565, 10). Returns (None,None,None) for PIN-form ids."""
    parts = str(pin).split("/")
    if len(parts) != 3:
        return (None, None, None)
    try:
        return tuple(int(p) for p in parts)
    except ValueError:
        return (None, None, None)


def gt_class(rec):
    return GT_CLASS_BY_TYPE.get(rec.get("gt_type"), "unknown")


def is_calibration_eligible(rec):
    return rec.get("gt_type") in CALIBRATION_TIERS


def validate_record(rec):
    """Return a list of human-readable issues ([] == valid)."""
    issues = []
    for f in REQUIRED_FIELDS:
        if f not in rec or rec[f] in (None, ""):
            issues.append(f"missing required field: {f}")
    gt = rec.get("gt_type")
    if gt is not None and gt not in GT_TYPES:
        issues.append(f"gt_type {gt!r} not in {GT_TYPES}")
    # gt_class, if present, must agree with the tier (don't conflate sale vs opinion).
    if "gt_class" in rec and gt in GT_CLASS_BY_TYPE and rec["gt_class"] != GT_CLASS_BY_TYPE[gt]:
        issues.append(f"gt_class {rec['gt_class']!r} disagrees with {gt} "
                      f"(expected {GT_CLASS_BY_TYPE[gt]!r})")
    if not isinstance(rec.get("gt_value"), (int, float)) or rec.get("gt_value", 0) <= 0:
        issues.append("gt_value must be a positive number")
    a = rec.get("attrs") or {}
    if a.get("finish_tier") not in (None,) + FINISH_TIERS:
        issues.append(f"attrs.finish_tier {a.get('finish_tier')!r} not in {FINISH_TIERS}")
    if a.get("condition") not in (None,) + CONDITIONS:
        issues.append(f"attrs.condition {a.get('condition')!r} not in {CONDITIONS}")
    z, s, b = parse_pin(rec.get("pin", ""))
    if z is None and not str(rec.get("pin", "")).isdigit():
        issues.append(f"pin {rec.get('pin')!r} is neither z/s/b nor a numeric PIN")
    return issues


def load_corpus(path=None):
    """Load the GT corpus. Defaults to the local (gitignored) data file; falls back to
    the committed template with a clear flag if the local file is absent."""
    used_template = False
    if path is None:
        if os.path.exists(LOCAL_PATH):
            path = LOCAL_PATH
        else:
            path = TEMPLATE_PATH
            used_template = True
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    records = data["records"] if isinstance(data, dict) and "records" in data else data
    return records, {"path": path, "used_template": used_template, "n": len(records)}


def save_corpus(records, path=None):
    """Persist the corpus as UTF-8 JSON (Arabic preserved). Defaults to the local file."""
    path = path or LOCAL_PATH
    payload = {"schema_version": 1, "records": records}
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)
    return path


def summarize(records):
    """ASCII-only summary (safe for the Windows cp1252 console)."""
    by_tier = {}
    for r in records:
        by_tier[r.get("gt_type", "?")] = by_tier.get(r.get("gt_type", "?"), 0) + 1
    elig = sum(1 for r in records if is_calibration_eligible(r))
    lines = [
        f"corpus rows: {len(records)}",
        "by tier: " + ", ".join(f"{k}={v}" for k, v in sorted(by_tier.items())),
        f"calibration-eligible (GT-1/GT-2): {elig}",
        f"calibration UNLOCKS at n>=20 eligible -> {'YES' if elig >= 20 else f'NO (need {20 - elig} more)'}",
    ]
    invalid = [(r.get("id"), validate_record(r)) for r in records]
    invalid = [(i, iss) for i, iss in invalid if iss]
    if invalid:
        lines.append("INVALID rows:")
        for i, iss in invalid:
            lines.append(f"  {i}: {'; '.join(iss)}")
    else:
        lines.append("all rows valid")
    return "\n".join(lines)


if __name__ == "__main__":
    recs, meta = load_corpus()
    tag = " (TEMPLATE — local data file absent)" if meta["used_template"] else ""
    print(f"loaded {meta['n']} rows from {os.path.basename(meta['path'])}{tag}")
    print(summarize(recs))

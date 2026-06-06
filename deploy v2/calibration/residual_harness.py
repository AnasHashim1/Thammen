"""
Residual harness + Lever-2 what-if (Sprint B-2 prep, INTERIM) — (3), READ-ONLY.

Runs the REAL live engine over the GT corpus and reports:
  - thammen_estimate + residual per property (DEFAULT flow AND with-correct-attrs flow),
  - residual per E4 stratum + the systematic over/under-anchor bias (calibration-eligible
    GT-1/GT-2 only),
  - a READ-ONLY Lever-2 what-if (down-re-anchor of old stock toward the a21 land floor).

Changes NOTHING (no engine/method change, no value shipped, no Heroku). Hits the live product
over HTTP because (a) the deployed a25 engine IS the real evaluate_unified path and (b) khazna
GIS is geo-restricted from here. POST uses a browser User-Agent (Cloudflare 1010-blocks bare
urllib POST — Operational Rule #61).

DISCIPLINE (HARD): n<20 GT-2 -> this MOTIVATES, it does NOT calibrate. No coefficient is fit.
Writes a UTF-8 report (Windows console is cp1252 -> Arabic to the file, ASCII to stdout).
"""

import json
import os
import subprocess
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import corpus_schema as cs
from lever2_simulation import simulate_lever2_reanchor

BASE = "https://thammen.qa"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
HERE = os.path.dirname(os.path.abspath(__file__))
REPORTS_DIR = os.path.join(HERE, "reports")


# ── formatting helpers (avoid f-string backslashes; cp1252-safe ASCII dashes) ──
def money(x):
    return f"{x:,}" if isinstance(x, (int, float)) else "-"


def pct(x):
    return f"{x}" if x is not None else "-"


def _stratum(s):
    """Render the dominant-stratum dict compactly (name + n + share), not the raw dict."""
    if isinstance(s, dict):
        nm = s.get("name") or s.get("label_ar") or "?"
        return f"{nm} (n={s.get('n')}, {s.get('share_pct')}%)"
    return s or "-"


def _post(path, payload, timeout=45):
    """POST JSON via curl (browser-UA, Rule #61). Returns (dict|None, error|None)."""
    url = BASE + path
    try:
        proc = subprocess.run(
            ["curl", "-s", "--max-time", str(timeout), "-A", UA,
             "-H", "Content-Type: application/json", "-X", "POST", url,
             "-d", json.dumps(payload)],
            capture_output=True, text=True, encoding="utf-8",
        )
    except Exception as e:
        return None, f"curl failed: {e}"
    if proc.returncode != 0:
        return None, f"curl rc={proc.returncode}: {(proc.stderr or '').strip()[:200]}"
    body = (proc.stdout or "").strip()
    try:
        return json.loads(body), None
    except Exception:
        return None, f"non-JSON response: {body[:160]}"


def _g(d, *path, default=None):
    cur = d
    for k in path:
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur[k]
    return cur


def _land_floor(resp):
    """a21 land floor: prefer valuation.value_floor.land_floor, else the decomposition land."""
    f = _g(resp, "valuation", "value_floor", "land_floor")
    if f is None:
        f = _g(resp, "valuation", "value_decomposition", "land", "estimated_qar")
    return f


def _extract(resp):
    v = resp.get("valuation") or {}
    return {
        "amount": v.get("amount"),
        "method": v.get("method"),
        "n_transactions": v.get("n_transactions"),
        "land_floor": _land_floor(resp),
        "dominant_stratum": _g(resp, "stock_strata", "dominant_stratum"),
        "accuracy_tier": _g(resp, "accuracy", "tier"),
        "muc_level": _g(resp, "material_uncertainty", "level"),
        "condition_note": bool(v.get("condition_note_ar")),
        "engine_version": resp.get("engine_version"),
    }


def _details_payload(rec):
    z, s, b = cs.parse_pin(rec["pin"])
    p = {"zone": z, "street": s, "building": b}
    a = rec.get("attrs") or {}
    for src, dst in [("condition", "condition"), ("is_luxury", "is_luxury"),
                     ("building_age_years", "building_age_years"),
                     ("floors", "floors"), ("footprint_m2", "footprint_m2")]:
        if a.get(src) is not None:
            p[dst] = a[src]
    return p


def _resid_pct(amount, gt):
    if amount is None or not gt:
        return None
    return round((amount - gt) / gt * 100, 1)


def _is_old(rec):
    a = rec.get("attrs") or {}
    return (a.get("building_age_years") or 0) > 10


def run():
    records, meta = cs.load_corpus()
    if meta["used_template"]:
        print("WARNING: local corpus absent — running on the TEMPLATE (synthetic). "
              "Add real GT to gt_corpus.local.json.")
    rows = []
    engine_seen = set()
    for rec in records:
        z, s, b = cs.parse_pin(rec["pin"])
        row = {"rec": rec, "default": None, "attrs": None, "err": None, "lever2": None}
        if z is None:
            row["err"] = "PIN-form id (engine reality-stops on PIN for built villas) — skipped"
            rows.append(row)
            continue

        base_resp, e1 = _post("/api/evaluate", {"zone": z, "street": s, "building": b})
        attr_resp, e2 = _post("/api/evaluate/details", _details_payload(rec))
        if e1 and e2:
            row["err"] = f"both calls failed: {e1} / {e2}"
            rows.append(row)
            continue
        if base_resp:
            row["default"] = _extract(base_resp)
            if row["default"]["engine_version"]:
                engine_seen.add(row["default"]["engine_version"])
        if attr_resp:
            row["attrs"] = _extract(attr_resp)
            if row["attrs"]["engine_version"]:
                engine_seen.add(row["attrs"]["engine_version"])

        src = row["attrs"] or row["default"] or {}
        a = rec.get("attrs") or {}
        row["lever2"] = simulate_lever2_reanchor(
            headline_amount=src.get("amount"),
            land_floor=src.get("land_floor"),
            building_age_years=a.get("building_age_years"),
            is_luxury_finish=bool(a.get("is_luxury")),
        )
        rows.append(row)

    _write_report(rows, engine_seen)
    _print_summary(rows, engine_seen, meta)
    return rows


def _bias(rows):
    elig = [r for r in rows if cs.is_calibration_eligible(r["rec"]) and r["default"]]

    def grp(pred):
        vals = [_resid_pct(r["default"]["amount"], r["rec"]["gt_value"])
                for r in elig if pred(r["rec"])]
        vals = [v for v in vals if v is not None]
        if not vals:
            return None
        vals.sort()
        n = len(vals)
        med = vals[n // 2] if n % 2 else (vals[n // 2 - 1] + vals[n // 2]) / 2
        return {"n": n, "mean": round(sum(vals) / n, 1), "median": round(med, 1)}

    return {
        "all_eligible": grp(lambda rec: True),
        "new_luxury": grp(lambda rec: (rec.get("attrs") or {}).get("luxury_new")),
        "old_stock": grp(lambda rec: _is_old(rec) and not (rec.get("attrs") or {}).get("luxury_new")),
    }


def _write_report(rows, engine_seen):
    os.makedirs(REPORTS_DIR, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
    path = os.path.join(REPORTS_DIR, f"residual_report_{ts}.md")
    eligible_n = sum(1 for r in rows if cs.is_calibration_eligible(r["rec"]))
    L = []
    L.append("# Calibration residual report (INTERIM — READ-ONLY, no engine change)\n")
    L.append(f"- run: {ts}  ·  engine: {', '.join(sorted(engine_seen)) or 'n/a'}  ·  live: {BASE}")
    L.append(f"- corpus rows: {len(rows)}  ·  calibration-eligible (GT-1/GT-2): {eligible_n}")
    L.append(f"- **DISCIPLINE: n={eligible_n} < 20 -> MOTIVATES, does NOT calibrate. "
             "No coefficient fit. GT-3/GT-4 = directional only.**\n")

    L.append("## Per-property residual (default flow vs with-correct-attrs)\n")
    L.append("| id | pin | district | tier | GT | engine(default) | resid% | engine(+attrs) | resid% | method | dominant stratum | land floor |")
    L.append("|---|---|---|---|---:|---:|---:|---:|---:|---|---|---:|")
    for r in rows:
        rec = r["rec"]
        if r["err"]:
            L.append(f"| {rec['id']} | {rec['pin']} | {rec['district']} | {rec['gt_type']} | "
                     f"{money(rec['gt_value'])} | - | - | - | - | ERR | {r['err']} | - |")
            continue
        d = r["default"] or {}
        a = r["attrs"] or {}
        rd = _resid_pct(d.get("amount"), rec["gt_value"])
        ra = _resid_pct(a.get("amount"), rec["gt_value"])
        L.append(
            f"| {rec['id']} | {rec['pin']} | {rec['district']} | {rec['gt_type']} | "
            f"{money(rec['gt_value'])} | {money(d.get('amount'))} | {pct(rd)} | "
            f"{money(a.get('amount'))} | {pct(ra)} | {d.get('method') or '-'} | "
            f"{_stratum(d.get('dominant_stratum'))} | {money(d.get('land_floor'))} |")

    bias = _bias(rows)
    L.append("\n## Systematic bias — calibration-eligible (GT-1/GT-2) only\n")
    L.append("| cohort | n | mean resid% | median resid% |")
    L.append("|---|---:|---:|---:|")
    for k in ("all_eligible", "new_luxury", "old_stock"):
        g = bias[k]
        if g:
            L.append(f"| {k} | {g['n']} | {g['mean']} | {g['median']} |")
        else:
            L.append(f"| {k} | 0 | - | - |")
    L.append("\n(negative = engine UNDER-anchors vs GT; positive = OVER-anchors. "
             "Illustrative until n>=20.)\n")

    L.append("## Lever-2 what-if (READ-ONLY simulation — SHIPS NOTHING)\n")
    L.append("Proposed B-2 Lever-2: down-re-anchor OLD stock toward the a21 land floor "
             "(MODERATE: floor+0-10%; luxury-finish exception: floor+~20%). Does it close the over-anchor?\n")
    L.append("| id | age | luxury finish | headline | land floor | sim re-anchor low/pt/high | rule | dpt% | target band |")
    L.append("|---|---:|---|---:|---:|---|---|---:|---|")
    any_old = False
    for r in rows:
        rec = r["rec"]
        l2 = r.get("lever2")
        a = rec.get("attrs") or {}
        if not l2 or not _is_old(rec):
            continue
        any_old = True
        src = r["attrs"] or r["default"] or {}
        if rec.get("analyst_clearing_low"):
            target = f"clearing {money(rec['analyst_clearing_low'])}-{money(rec['analyst_clearing_high'])}"
        else:
            target = f"GT {money(rec['gt_value'])}"
        if l2["applies"]:
            band = f"{money(l2['reanchored_low'])}/{money(l2['reanchored_point'])}/{money(l2['reanchored_high'])}"
            L.append(f"| {rec['id']} | {a.get('building_age_years')} | {bool(a.get('is_luxury'))} | "
                     f"{money(src.get('amount'))} | {money(src.get('land_floor'))} | {band} | "
                     f"{l2['rule']} | {pct(l2['delta_point_pct'])} | {target} |")
        else:
            L.append(f"| {rec['id']} | {a.get('building_age_years')} | {bool(a.get('is_luxury'))} | "
                     f"{money(src.get('amount'))} | {money(src.get('land_floor'))} | no fire | "
                     f"- | - | {l2['reason']} |")
    if not any_old:
        L.append("| - | - | - | - | - | (no old-stock entries) | - | - | - |")
    L.append("\n> Lever-1 (UP finish/new-build premium) is NOT simulated: corpus-gated "
             "(local `luxury_new` MoJ stratum n=0 -> calibrate cross-area from n>=20 GT-2).")

    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(L) + "\n")
    print(f"report written: {os.path.relpath(path, HERE)}")
    return path


def _print_summary(rows, engine_seen, meta):
    print("-" * 64)
    print(f"engine: {', '.join(sorted(engine_seen)) or 'n/a'}  (expect a25)")
    print(f"corpus: {meta['n']} rows from {os.path.basename(meta['path'])}")
    for r in rows:
        rec = r["rec"]
        if r["err"]:
            print(f"  {rec['id']:5} {rec['pin']:12} {rec['gt_type']:5}  ERR: {r['err'][:55]}")
            continue
        d = r["default"] or {}
        a = r["attrs"] or {}
        rd = _resid_pct(d.get("amount"), rec["gt_value"])
        ra = _resid_pct(a.get("amount"), rec["gt_value"])
        print(f"  {rec['id']:5} {rec['pin']:12} {rec['gt_type']:5} GT={money(rec['gt_value']):>9} "
              f"default={money(d.get('amount')):>9} ({pct(rd)}%)  +attrs={money(a.get('amount')):>9} ({pct(ra)}%)")
        l2 = r.get("lever2") or {}
        if _is_old(rec):
            if l2.get("applies"):
                print(f"        Lever-2 sim ({l2['rule']}): -> {money(l2['reanchored_point'])} ({pct(l2['delta_point_pct'])}%)")
            else:
                print(f"        Lever-2 sim: no fire ({(l2.get('reason') or '')[:50]})")
    eligible_n = sum(1 for r in rows if cs.is_calibration_eligible(r["rec"]))
    tail = "CALIBRATABLE" if eligible_n >= 20 else f"MOTIVATES ONLY (need {20 - eligible_n} more)"
    print(f"calibration-eligible (GT-1/GT-2): {eligible_n}  -> {tail}")
    print("-" * 64)


if __name__ == "__main__":
    run()

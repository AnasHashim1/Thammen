# CHANGELOG v72 — Sprint 2.22.0a.20 (A7): `rics_compliant` honest status label

**Engine:** `thammen-sprint2p22p0a20-rics-compliant-status-label`
**SPRINT_TAG:** `2.22.0a.20`  ·  **api/health:** `3.1.0-sprint2.22.0a.20`
**Date:** 2026-06-03
**Files changed (backend only):** `material_uncertainty.py`, `evaluate_unified.py`,
`output_briefs.py`, `test_sprint_2_22_0a20.py` (new)
**`api.py` + `index.html`:** UNTOUCHED (backend-only — R14 N/A-by-construction)
**Class of change:** DISPLAY / LABEL ONLY — **no valuation logic, every value byte-identical.**
Gate 2 satisfied by the signed brief (verbatim copy below).

---

## 1. Why this matters

The JSON field `material_uncertainty.rics_compliant` is always `false` on the
villa/land/refusal paths. Read bare, `false` looks like **"non-compliant"** — which
is misleading. It is `false` **by design**: the AVM **methodology** already follows
the RICS Red Book (Sales Comparison **VPS 3 / IVS 103**, valuation models
**VPS 5 / IVS 105**, material uncertainty **VPGA 10**, reporting **VPS 6 / IVS 106** —
surfaced in the live `rics_methodology_note`). The bool is gated on
`has_field_inspection` (`material_uncertainty.py:382`), which an AVM never has, so what
is actually pending is the **licensed-valuer review / sign-off (Stage 5, per IVS 105)**
that turns an AVM output into a formally compliant valuation. The field must read
**"review pending," NOT "non-compliant."**

A7 was closed as *not-a-bug / by-design* in Sprint 2.22.0a.8 (the bool logic is
correct); the remaining work — surfacing an honest companion label so a consumer
reading the JSON isn't misled — is this sprint. Beta-credibility quick-win.

## 2. Recon findings (R-PROTOCOL)

- **Every surface of `rics_compliant` is JSON, not rendered.** `index.html`'s
  `case 'material_uncertainty'` renderer (`:1493`) emits only `level`, `factors`,
  `recommendations` — it **ignores `rics_compliant`**; and every generic/fallback dump
  (`:1510`, `:1687`) handles string/number/array only, so a **boolean is skipped**. The
  bare bool renders **nowhere** in the UI. The honest "field inspection needed for RICS
  compliance" disclosure **already renders** via `recommendations` (appended at
  `material_uncertainty.py:385`). ⟹ this fix is **backend-only**; the UI was already honest.
- **JSON emission sites:** root `material_uncertainty.rics_compliant` —
  (a) fast/refusal paths via the `_enrich_material_uncertainty` chokepoint
  (`evaluate_unified.py:1922`, 6 callers); (b) main valuation path via the v3 dict
  (`evaluate_v3.py:462` → copied at `evaluate_unified.py:4714`). Plus the brief
  `content.rics_compliant` (buyer + valuer, `output_briefs.py:595/933`).
- **Only one downstream LOGIC read:** `material_uncertainty.py:385 if not rics_compliant:`
  appends a recommendation (display, not valuation). **Left untouched** — semantics preserved.
- **Wording check (brief-requested):** Stage 5 is defined as licensed-valuer
  **review / sign-off** (`2p22p0_pre/CHANGELOG_pre_2p22p0_v2.md:79`: "reviews Stage 1-4
  output, performs independent field verification, and **signs**"), and the **live**
  `rics_methodology_note_ar` already ends «… دون **مراجعة مُقيِّم مُرخّص (المرحلة الخامسة)**».
  The signed copy is that exact phrase + «بانتظار» → verbatim-consistent. **"review/مراجعة"
  is correct; no flag-back.**

## 3. What this patch does

New canonical helper in `material_uncertainty.py` (home of the bool):

```python
RICS_COMPLIANT_STATUS_PENDING_AR = 'بانتظار مراجعة مُقيِّم مُرخّص (المرحلة الخامسة)'
RICS_COMPLIANT_STATUS_PENDING_EN = 'Pending licensed-valuer review (Stage 5)'

def rics_compliant_status_fields(is_compliant) -> dict:
    if is_compliant:
        return {}                       # True is not misleading; no unsigned copy invented
    return {'rics_compliant_status_ar': RICS_COMPLIANT_STATUS_PENDING_AR,
            'rics_compliant_status_en': RICS_COMPLIANT_STATUS_PENDING_EN}
```

Wired (spread/merge, never clobbering a caller key) at every JSON surface of the bool:

| Surface | Site | Mechanism |
|---|---|---|
| Root MU — fast/refusal paths (all 6) | `evaluate_unified._enrich_material_uncertainty` | `setdefault` from `out['rics_compliant']` |
| Root MU — main valuation path | `evaluate_unified.py:4714` (after the v3 dict copy) | guarded `setdefault`; survives the downstream factor/level mutations (they never touch `rics_compliant`) |
| Brief MU section (buyer + valuer) | `output_briefs.py:595/933` | `**rics_compliant_status_fields(unc.get('rics_compliant', False))` |

**Status emitted only when the bool is `False`** (the pending/misleading case). `True`
(hybrid Lusail) emits nothing — `true` is not misleading and the signed copy covers only
the pending case (no unsigned "compliant" string invented). `None`/malformed → pending
(**fail-safe to disclosure**, consistent with the a17/a19 condition-note ethos). The AR
copy contains **no Latin** → no LRM/bidi handling needed. Every injection is wrapped /
`setdefault`-guarded so a label failure can never break `evaluate`.

**The `rics_compliant` bool is unchanged everywhere; no value, level, method, tier, MUC,
or decision is touched.** This sprint only ADDS two string keys next to the bool.

## 4. Verification — empirical evidence

- **py_compile** 3/3 OK.
- **Isolated** `test_sprint_2_22_0a20.py` **20/20** — imports the PRODUCTION helper +
  `_enrich_material_uncertainty` + real `generate_brief` (Rule #40 / E14): false→both signed
  keys verbatim; true→{}; None→pending; AR no-Latin; enrich preserves the bool + level +
  doesn't mutate input + no-clobber; buyer/valuer brief sections carry/omit the status correctly.
- **DoD matrix:** aggregator **392/392** · security **15/15** · surface-honesty **45/45** ·
  broad `2p22p0_pre/run_regression_2p22p0a.py` **63/63** (62→63, +1 = the new test; genuine
  clean pass, 87.3s — the a17 geometric-determinism flake-split holds).
- **Local E2E (live GIS)** — production `evaluate_thammen`, signed trio, **zero value drift**:

| PIN | method | amount (= a19) | rics_compliant | status_ar (root + brief) |
|---|---|---|---|---|
| 54/541/6 Marikh | comparison_thin | **5,400,000** | False (unchanged) | PRESENT |
| 56/565/21 Abu Hamour | comparison_bracket | **2,400,000** | False (unchanged) | PRESENT |
| 52/903/90 apt | insufficient_data | **None** | False (unchanged) | PRESENT (root; refusal fast-brief has no MU section) |

## 5. Deployment

```
cd /d "C:\Thammen\deploy v2"
git add material_uncertainty.py evaluate_unified.py output_briefs.py test_sprint_2_22_0a20.py CHANGELOG_v72.md
git commit -m "Sprint 2.22.0a.20 (A7): rics_compliant honest status label"
git subtree push --prefix "deploy v2" heroku master
git push origin master
```

## 6. Post-deploy verification (browser-UA curl, Rule #61)

```
curl -s -A "Mozilla/5.0 ... Chrome/120 Safari/537.36" https://thammen.qa/api/health
curl -s -A "Mozilla/5.0 ... Chrome/120 Safari/537.36" -X POST https://thammen.qa/api/evaluate ^
  -H "Content-Type: application/json" -d "{\"zone\":56,\"street\":565,\"building\":21}"
```
Expect: engine a20; villa 56/565/21 = 2,400,000 + `material_uncertainty.rics_compliant_status_ar`
present; trio values byte-identical to a19.

## 7. What's NOT in this patch (scope boundary)

- **No `index.html` change** — the bool never rendered; the UI is already honest via the
  rendered `recommendations`. (The signed status sits in the JSON next to the bool.)
- **No bool/logic change** — `rics_compliant` stays gated on `has_field_inspection`
  (`material_uncertainty.py:382`); the `if not rics_compliant:` recommendation
  (`:385`) is untouched. A7 stays *closed-as-by-design* on the bool; this only adds the label.
- **No field rename** — the bool keeps its name (Rule #47: rename is its own pass);
  the honest reading now rides on the adjacent status string.
- **The durable R7 condition axis** (built-type / condition) remains **Sprint B**.

---
*Sprint 2.22.0a.20 — A7 honest status label. Backend-only, display/label only, zero value drift.*

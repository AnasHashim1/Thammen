# CHANGELOG — Sprint 2.9: Neutral Direction Fix (R2 Zoning UI Bug)

**Engine version:** `thammen-sprint2p9-neutral-direction`
**Date:** 2026-05-13
**Files changed:** `api.py`, `evaluate_unified.py`
**Builds on:** Sprint 2.7 (v13)

---

## Why this matters

A live UI audit of five real Qatari properties cross-referenced with
Qatar GIS revealed that **every R2-zoned property in Qatar** showed
the zoning factor with a red error background:

> 🟥 `✗ منطقة سكنية (R2)`  ← rendered as a negative feature

R2 is **standard residential zoning**, not a defect. It covers an
estimated 19,050 zoning polygons in Qatar (~13.2% of all zoned land,
verified via GIS `Vector/Zoning` count). For every owner in those
zones, thammen has been visually telling them their zoning is a
problem since the location-features UI was added.

## Root cause

`evaluate_unified.py:2764` and `api.py:289` both used:

```python
is_positive = direction == 'positive'
```

This Python expression returns `False` whenever `direction` is
`'neutral'`. The JSON serializer wrote `"positive": false`, and the
frontend at `index.html:681` rendered that value with the
`loc-neg` (red error) CSS class:

```javascript
const cls = f.positive===true ? 'loc-pos'        // green
          : f.positive===false ? 'loc-neg'       // red ← neutral fell here
          :                      'loc-neu';      // gray (never reached)
```

R1 (`weight=+0.020`) got `direction='positive'` → green ✓ correctly.
R2 (`weight=0.000`)  got `direction='neutral'`  → red ✗ wrongly.
R3 (`weight=-0.020`) got `direction='negative'` → red ✗ correctly.

The frontend already handled the gray (`loc-neu`) case — but only
when `positive` was `null` / `undefined`, which the backend never sent.

## What this patch does

### Backend (`evaluate_unified.py:2755-2778`)

Replaces the two-state boolean with explicit three-state logic:

```python
# Sprint 2.9: 3-state direction.
if direction == 'positive':
    is_positive = True
elif direction == 'negative':
    is_positive = False
else:  # 'neutral' / missing / unknown
    is_positive = None
```

The `plot_shape` override block is preserved unchanged — it still
forces `True`/`False` for the regular/irregular shape labels.

### Backend (`api.py:288-298`)

Same fix applied to the v2 fallback path. Both code paths now emit
`positive: null` for neutral factors. No other behavior change.

### Frontend

**Zero changes.** The existing tri-state classifier in `index.html`
(`positive===true ? 'loc-pos' : positive===false ? 'loc-neg' : 'loc-neu'`)
already handled `null` correctly — the fix simply unblocks the
already-existing neutral codepath.

---

## Verification — empirical evidence

### Methodology
Live audit of 5 properties cross-referenced with Qatar GIS:

| Address | GIS district | GIS zoning | thammen district | thammen zoning text | R2 issue? |
|---|---|---|---|---|---|
| 52/903/90 | اللقطة | R2 | اللقطة ✓ | `منطقة سكنية (R2)` | 🔴 RED before / ⚪ NEUTRAL after |
| 56/565/21 | بو هامور | R1 | بو هامور ✓ | `منطقة سكنية خاصة (R1)` | ✓ green (unchanged) |
| 54/541/6 | المريخ الجنوبي | R1 | المريخ الجنوبي ✓ | `منطقة سكنية خاصة (R1)` | ✓ green (unchanged) |
| 51/835/17 | الغرافة | R1 | (compound — no UI card) | — | n/a |
| 70/770/11 | الخيسة | R1 | الخيسة ✓ | `منطقة سكنية خاصة (R1)` | ✓ green (unchanged) |

### Scope of impact (Qatar GIS counts)

| ZONING code | # polygons | % of zoned land | Before patch | After patch |
|---|---|---|---|---|
| R1 / R1-TYP | 120,779 | ~84.0% | 🟢 green ✓ | 🟢 green ✓ |
| R2 | **19,050** | **~13.2%** | 🔴 RED ✗ (BUG) | ⚪ neutral ✓ |
| R3 | 3,947 | ~2.7% | 🔴 red ✗ (correct — dense) | 🔴 red ✗ (unchanged) |

About **1 in 8 Qatari properties** are no longer mis-painted.

### Unit-test matrix (direction → UI)

| direction | old (buggy) | new (fixed) | UI class | UI icon | Color |
|---|---|---|---|---|---|
| positive | True | True | loc-pos | ✓ | 🟢 أخضر |
| negative | False | False | loc-neg | ✗ | 🔴 أحمر |
| neutral | False (BUG) | None | loc-neu | — | ⚪ رمادي |
| missing/unknown | False (BUG) | None | loc-neu | — | ⚪ رمادي |

### plot_shape override regression test

| label | direction | result | Expected |
|---|---|---|---|
| قطعة منتظمة الشكل | neutral | True | True ✓ |
| قطعة غير منتظمة | neutral | False | False ✓ |

---

## Deployment

```cmd
cd /d "C:\Thammen\deploy v2"
copy /Y api.py api.py.bak4 && copy /Y evaluate_unified.py evaluate_unified.py.bak9
tar -xf "%USERPROFILE%\Downloads\sprint2p9-neutral-direction.zip"
findstr /C:"Sprint 2.9" api.py evaluate_unified.py
git add api.py evaluate_unified.py CHANGELOG_v14.md
git commit -m "Sprint 2.9: 3-state direction (R2 zoning no longer rendered as error)"
git push heroku master
```

## Verification curl

```bash
# Property 52/903/90 (اللقطة, R2) — should now show R2 as neutral (positive=null)
curl -s -X POST https://thammen.qa/api/evaluate \
  -H "Content-Type: application/json" \
  -d '{"zone":52,"street":903,"building":90,"audience":"buyer"}' \
  | jq '.location_features[] | select(.label | contains("R2"))'

# Expected (after patch):
# { "label": "منطقة سكنية (R2)", "positive": null }
```

In the UI, the R2 chip should now appear with a gray background and
an "—" icon instead of red with a "✗" icon.

## What's NOT in this patch (intentional Sprint 2.9 scope)

- **Bug #1 (تزوير label_ar)** — confirmed not visible in UI thanks to
  defensive `LABEL_FIXES` in two places. Pure technical debt; not
  user-facing. Filed for future cleanup as Sprint 2.9b.
- **Bug #2 (reconciliation divergence on 10-Year Rule)** — confirmed
  not surfaced in the UI (no rendering code references `reconciliation`).
  3 of 5 audited properties had `divergence` flagged in JSON, but no
  user has ever seen the "تباين كبير ⚠️" warning. Filed as Sprint 2.11.
- **PD_NO=0 + standalone_villa classification** (e.g. 56/565/21) —
  may be either a misclassification or legitimate (some standalone
  villas have undivided cadastres). Needs ground inspection before
  any patch. Filed as Sprint 2.10 (after Asset Type Selection).
- **District name "امريخ الجنوبي"** (should be "المريخ الجنوبي") —
  comes from GIS source data, not thammen. Future enhancement: a
  normalization map for known GIS typos.

## Methodological note

This sprint replaces an audit-by-JSON-inspection finding (the
original Bug #8 in the audit list) with audit-by-UI-cross-reference:
- Looked at what the user actually sees in the browser
- Verified the bug against Qatar GIS ground truth
- Quantified scope (19,050 polygons, ~13.2% of Qatar)
- One-line root cause, two-line fix per file

Future audits should follow this same pattern: **render in browser
first, claim "critical" second**.

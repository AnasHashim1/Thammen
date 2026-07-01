# CHANGELOG v165 — Sprint 2.22.0b.84 «توائم الإنجليزية لتفكيك القيمة» (EN twins — the value-decomposition note bodies)

**Engine:** `thammen-sprint2p22p0b84-en-decomposition-twins` · **SPRINT_TAG** `2.22.0b.84` · **api-health** `3.1.0-sprint2.22.0b.84`
**Files:** `evaluate_unified.py` (`_decompose_value` + `_reconcile_decomposition_narrative` — additive `*_en` keys + the version bump) · `test_sprint_2_22_0b84.py` (NEW)
**Class:** 🟢 BACKEND-ONLY / **VALUE-INVARIANT** — additive `*_en` dict keys alongside the untouched `*_ar`; EN dormant (the frontend reads them via `pick()` only when `LANG==='en'`, b77, `EN_ENABLED=false`). `api.py` + `index.html` UNTOUCHED → **R14 N/A by construction** (the b59/b71/§20.18 precedent). The AR output is byte-identical.

## 1. Why this matters

The EN-localization track wired the whole result-family **chrome** (labels/titles) through b80–b83, and the b78 backend catalog authored `_en` for the main-figure note bodies (condition / cost / hbu / age-honesty / resurvey / leadership / land-floor / vintage / rics-note / MUC clause / refusal message / …). The **value-decomposition detail block** (the «تفكيك القيمة» tile in the result-screen «التفاصيل الكاملة» accordion + the full report) still emitted its interpretation/methodology/confidence notes in Arabic only — so in EN mode those three `pick()` reads (`pick(bd,'interpretation')`, `pick(vd,'methodology_note')`, `pick(ld,'confidence')`) fell back to Arabic. b84 authors their `_en` twins. First unit of the backend-`_en`-twins track (the b83 carried-forward).

## 2. Root cause

`_decompose_value` (evaluate_unified.py) built `land.confidence_ar`, `building_implied.interpretation_ar` (5 status branches), and `methodology_note_ar` with no `_en` sibling; `_reconcile_decomposition_narrative` (b14/ISS-A07) then **overwrites** `interpretation_ar` for Case A / Case C — so an EN twin set only at build time would go stale after the reconcile.

## 3. What this patch does

- `_decompose_value`: `land_conf_en` (mirror of `land_conf_ar`: reliable→"Sufficient evidence" / indicative→"Limited evidence" / thin→"Insufficient evidence"); an `interp_en` block keyed on `status` mirroring all five `interp` branches (same `bld_pct` number, `:.1f`); and `methodology_note_en`. Return dict gains `land.confidence_en`, `building_implied.interpretation_en`, `methodology_note_en`.
- `_reconcile_decomposition_narrative`: **Case A** and **Case C** now also set `building_implied.interpretation_en` (mirroring the overwritten `interpretation_ar`), so AR and EN stay consistent after the reconcile. Case A's EN uses `dom.get('label_en') or dom.get('label_ar')` for the dominant-stratum label (the strata `label_en` lands in a later sprint — graceful AR fallback until then) + an English share string. Case B keeps the build-time twin (unchanged). The dominant-stratum `note_en` cross-line is deferred to the stock-strata sprint (the base `note_en` is authored there).
- **No `_ar` value changed**; **no amount / range / method / % / decomposition number changed** — additive keys only.

**Personas (PO standing directive).** Linguist: professional English, register-consistent with the b78–b83 catalog. Lawyer: these are interpretation/methodology notes (not disclaimers); the EN preserves the protective "A licensed-valuer review is required" (land_exceeds_value branch) and the "per the RICS Red Book" attribution; no new claim, no weakened disclaimer.

## 4. Verification — empirical evidence

- Isolated `test_sprint_2_22_0b84.py` — exercises the REAL `_decompose_value` (4 reachable status branches — the 5th, `land_exceeds_value`, is dead behind the Patch-C guard) + `_reconcile_decomposition_narrative` (Case A + Case C): `_en` present + correct per branch, the `bld_pct` number carried into EN, confidence-tier mapping, **AR byte-identical**, value-math untouched (land/building/pct), and the Case-A EN is NOT the stale un-reconciled line. + the frontend `pick()` wiring intact.
- DoD: aggregator / security / surface / broad walk — **[run on Bash recovery]**.
- **R14 N/A by construction** — `index.html` git-confirmed UNTOUCHED; the three `pick()` reads shipped + R14-verified in b81/b83; the served render is a proven no-op on the AR path.

## 5. Deployment

```
git -C "C:/Thammen" subtree push --prefix "deploy v2" heroku master
git push origin master
```

## 6. Verification curl (post-deploy)

```
curl --compressed -s https://thammen.qa/api/health    # engine = …b84
curl --compressed -s -X POST https://thammen.qa/api/evaluate -H "Content-Type: application/json" \
  -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120 Safari/537.36" \
  -d '{"zone":54,"street":541,"building":6}' | python -c "import sys,json; vd=json.load(sys.stdin)['valuation'].get('value_decomposition') or {}; print('interp_en:', bool((vd.get('building_implied') or {}).get('interpretation_en')), '| methodology_note_en:', bool(vd.get('methodology_note_en')), '| land.confidence_en:', bool((vd.get('land') or {}).get('confidence_en')))"
```
+ the 5-fixture value byte-gate byte-identical to v255 (54/541/6 2,400,000 · 56/647/6 3,800,000 · 55/296/13 2,600,000 · 56/565/21 2,400,000 · 52/903/90 None).

## 7. What's NOT in this patch (carried forward, Rule #42)

- The remaining backend `_en` twins: the stock-strata card (`classification_label`/`reliability_label`/`sprint_scope_caveat`/`stratum_note`/`methodology`/`label`/dominant `note`), the audience-brief sections (output_briefs.py: `cap_rate_label`/`description`/`role`/`footer`/`body`/`recommendation`/`plausibility`/`caveat`/`rent_source`), the cost-stack `assumptions`/`unavailable_reason`, the substantiality `rationale`/`methodology_note`, scope `requires_user_input`/`guidance`/`requires`, scenarios `delta_label`, tier-breakdown `role`/`source` — each its own bounded value-invariant sprint.
- The **reveal** (`EN_ENABLED=true`) stays gated on the PO wording sign-off.
- No methodology / value / security change — additive i18n copy only.

# CHANGELOG v69 — Sprint 2.22.0a.17: Clean-Bracket Condition Caveat

**Engine:** `thammen-sprint2p22p0a17-clean-bracket-condition-caveat` · `/api/health` → `3.1.0-sprint2.22.0a.17`
**Date:** 2026-06-02
**Type:** **Copy-only, honesty-additive.** No valuation logic. All values byte-identical.
**Gate:** Rule #32 — Anas signed `docs/BRIEF_2p22p0a17_clean_bracket_condition_caveat.md`. Honesty-additive (more disclosure, conservative) → clears the valuation-honesty principle by construction. Reversible-but-user-visible → Full lane (not autonomous-lead).
**Files changed:** `evaluate_unified.py` (constants + `_condition_note_applies` predicate + clean-branch call + version bump), `index.html` (muted render under the range), `test_sprint_2_22_0a17.py` (new), `CHANGELOG_v69.md` (new). **`api.py` deliberately NOT touched** — its `/api/health` version is `f"3.1.0-sprint{SPRINT_TAG}"` and auto-tracks the bumped `SPRINT_TAG` (Rule #39 deviation vs the brief's file list; single source = `SPRINT_TAG`).

---

## 1. Why this matters (the gap)

The honest-range machinery already cushions the **dispersed** paths — widened/geo (a10) and dispersed reliable bracket cells (a14) — and the indicative/thin paths carry their own caveats. But **clean reliable bracket cells (pool ppm² dispersion < 0.30) are presented as a confident point estimate + a tight supporting range, with no honest-range and no condition flag.**

Condition-blindness (RISK_REGISTER **R7**, bidirectional) hits these cells too — and it is *invisible* there. Reference: Abu Hamour **56/565/21 = 2,400,000** (point, ~2.2–2.6M range, `comparison_bracket`, clean). A renovated subject is defensibly higher (~2.5–2.8M); a worn subject lower. Nothing on screen tells the user condition was not assessed.

**Key insight (from the brief §5 §2):** the dispersion gate measures *market spread among comps* — **orthogonal to the subject's condition**. A tight cell is tight only because its comps agree; if that stock is uniformly aged and the subject is renovated, the clean point still under-anchors. So the caveat must apply to **all** clean villa/house bracket points, not just near-gate ones.

**Frequency (brief §5, MoJ reconstruction calibrated to the engine's documented anchor):** **≈31% of villa lookups** (incidence-weighted; 16/34 reliable cells are clean ≈ 47% cell-level) land on a clean bracket point with no condition cushion. Decision rule "rare → ship as-is; common → cheap caveat" ⇒ common ⇒ add the caveat. The other ~69% already carry a cushion (honest-range / indicative / thin).

## 2. Root cause

The Stage-1 dispersion application block (`evaluate_unified.py`, `_build_unified_output`, the `try:` that runs last) acts **only on the gated branch**:

```python
if _g and _g['gated'] and _val.get('amount') is not None:
    _val['range_is_headline'] = True   # a10/a14 honest-range — dispersed only
    ...
```

The **clean** complement (a `comparison_bracket` result whose `_g` is present-but-not-gated, i.e. dispersion < 0.30) — and the **ambiguous** case (`_g is None` because the bracket's `ppm2_dispersion` was missing) — fell through with **no disclosure at all**. That is the gap.

## 3. What this patch does

### Backend (`evaluate_unified.py`)
- Two module-level strings (verbatim from the brief; Rule #54 skipped per the signed decision):
  - `CONDITION_NOTE_AR` = «لم تُؤخذ حالة العقار (تجديد أو تهالك) في الحسبان. عقار في حالة أفضل من المتوسط قد يقع أعلى هذه النقطة، وعقار في حالة أدنى قد يقع تحتها.»
  - `CONDITION_NOTE_EN` = "Property condition (renovation or wear) was not assessed. A better-than-average property may sit above this point; a poorer one may sit below."
- New pure predicate `_condition_note_applies(primary, gate, asset_type, amount) -> bool` (placed next to `_stage1_dispersion_gate`):
  - **Gets the note:** `method == 'comparison_bracket'` AND `asset_type ∈ {standalone_villa, house, villa}` AND `amount is not None` AND **not** dispersion-gated.
  - **Fail-safe TO DISCLOSURE:** uses `gate.get('gated')`, so a `None` **or malformed** gate (dispersion unresolved) → **include** the note (locked decision).
  - **Excluded by construction:** widened/geo (a10) + thin + indicative (by `method`); land + apartment/tower/commercial (by `asset_type`); refusals (no bracket amount).
- The clean-branch call sits in the same `try:` as the a14 gated block (so any error is swallowed — the note never breaks the evaluate path):
  ```python
  if _condition_note_applies(primary, _g, getattr(ev, 'asset_type', None), _val.get('amount')):
      _val['condition_note_ar'] = CONDITION_NOTE_AR
      _val['condition_note_en'] = CONDITION_NOTE_EN
      output['valuation'] = _val
  ```
- **No valuation logic touched.** The note is additive metadata on `valuation`; `amount`, `low`, `high`, `method`, ppm², window — all unchanged.

### Frontend (`index.html`)
Directly under the range block on the main valuation card, a muted neutral note (locked: `.rn`, not `--warn-bg`):
```javascript
if(v.condition_note_ar){h+='<div class="rn" style="margin-top:10px;font-size:.8rem">'+v.condition_note_ar+'</div>';}
```
`.rn` = the existing muted note class (`background:var(--alt); color:var(--muted); padding:14px; line-height:1.8`) — the same class already shipping for the range-expansion note on the result card. Pure Arabic; no LRM needed.

### Version
`ENGINE_VERSION` + `SPRINT_TAG` → a17. `api.py` derives `/api/health` from `SPRINT_TAG` (no literal edit).

## 4. Scope / gating

- **Note iff** `asset_type ∈ {standalone_villa, house, villa}` AND `method == 'comparison_bracket'` AND amount present AND not (`gate` gated). `house`/`villa` are forward-safe aliases — today a house subject classifies `standalone_villa` (no `house`/`villa` member in `AssetType`; §20.12), so `standalone_villa` is the live match.
- **Excluded (unchanged):** land, apartment/tower, dispersed bracket (a14 honest-range), indicative, thin, widened/geo (a10), refusals.
- **Backward compatible:** old clients ignoring `condition_note_*` keep working.

## 5. Verification — empirical evidence (measured 2026-06-02)

- **`py_compile`** `evaluate_unified.py` + `api.py` → exit 0.
- **Isolated logic** `test_sprint_2_22_0a17.py` → **15/15** (the 7 brief cases — clean villa PRESENT, widened/thin/land/apartment/dispersed ABSENT, fail-safe PRESENT — plus house/villa aliases, malformed-gate fail-safe, amount-None, none-primary, commercial; + 2 verbatim-wording guards). The test imports the **production** `_condition_note_applies` (Rule #40 / E14 — not a replica).
- **DoD regression matrix (re-measured, #58):** aggregator `run_sprint_2p22p0a_suite.py` **392/392** · security `test_sprint_2p16p17_security.py` **15/15** · `test_sprint_2p22p0a3_surface_honesty.py` **45/45** · broad `2p22p0_pre/run_regression_2p22p0a.py` **59/59** (58 prior + the new a17 test). The first broad pass reported 58/59 with `test_sprint_2p22p0a7_geometric_determinism.py` failing — the **known transient live-GIS flake** (§20.16, flaked in the a16 run too); **green on isolated re-run** (26 live points, HBU + E7/A11 anchors held, 0 mismatches). a17 touches no `geometric_factors`. `test_v2_modules.py` excluded (pytest not in requirements).
- **User-visible (checklist 5b):** `findstr /C:"condition_note_ar" index.html` → `index.html:936` (the render line) — confirms the key is rendered, not JSON-only.
- **`node --check`:** node not installed locally (§11.3 / a8 precedent). The added JS is a single self-contained `if(){...}` reusing the proven `.rn` class, inserted between complete statements; verified balanced by inspection. Live render confirmed post-deploy + Anas's mobile lane.
- **Mobile 390×844:** the note reuses `.rn` — an unconstrained block (padding, `line-height:1.8`, no fixed width, no `nowrap`) → Arabic wraps within the card, no horizontal overflow; same class/pattern already shipping for the result-card range-expansion note. Pixel-confirm = Anas's post-deploy lane (a16 precedent).
- **4-anchor live smoke:** post-deploy (browser-UA, §7 below).

## 6. Deployment (Windows cmd — one command per line, no `&&`; Rule #43 subtree push; Anas approves per #32)

```
cd /d "C:\Thammen\deploy v2"
copy /Y evaluate_unified.py evaluate_unified.py.bak_2p22p0a16
copy /Y index.html index.html.bak_2p22p0a16
git add evaluate_unified.py index.html test_sprint_2_22_0a17.py CHANGELOG_v69.md
git commit -m "Sprint 2.22.0a.17: clean-bracket condition caveat (copy-only, honesty-additive)"
git subtree push --prefix "deploy v2" heroku master
git push origin master
```

> Note vs brief §9: deploy is the **`git subtree push --prefix "deploy v2"`** form (Rule #43 — the repo root is `C:\Thammen`; a plain `git push heroku master` is rejected). `api.py` is **not** in `git add` (unchanged this sprint). `origin` backup follows the Heroku deploy (R1 ritual).

## 7. Post-deploy verification (browser-UA, Operational #61)

```
curl -s -A "Mozilla/5.0" -X POST https://thammen.qa/api/evaluate -H "Content-Type: application/json" -d "{\"zone\":56,\"street\":565,\"building\":21}" > a17_ah.json
findstr /C:"condition_note_ar" a17_ah.json
findstr /C:"2400000" a17_ah.json
curl -s -A "Mozilla/5.0" -X POST https://thammen.qa/api/evaluate -H "Content-Type: application/json" -d "{\"zone\":54,\"street\":541,\"building\":6}" > a17_marikh.json
findstr /C:"condition_note_ar" a17_marikh.json
curl -s https://thammen.qa/api/health
```

**Expected:** `a17_ah.json` matches `condition_note_ar` **and** `2400000` (value identical, note present); `a17_marikh.json` does **NOT** match `condition_note_ar` (widened honest-range path) and still shows 4,500,000; `/api/health` reports `…a17…`; 52/903/90 refusal unchanged.

## 8. What's NOT in this patch (scope boundary)

- No range widening / quantified condition band (heavier; overlaps Sprint B's built-type/condition work — deferred).
- No change to dispersed / indicative / thin / widened / land / apartment surfaces.
- No valuation-logic, ppm², or window change. Copy + one predicate only.
- `api.py` untouched (version auto-derives from `SPRINT_TAG`).
- Not the GIS-vs-thammen field-check half of the §5 audit (separate; gated on khazna allowlist + `index.html` upload).

# CHANGELOG v146 — Sprint 2.22.0b.65 «وسم اتجاه واعٍ بالتشتّت» (trend dispersion-aware label) — DEBUG #5

**Engine:** `thammen-sprint2p22p0b65-trend-dispersion-label` · **SPRINT_TAG** `2.22.0b.65` · **Date:** 2026-06-25
**Files:** `moj_reference.py` (compute_trend label + docstring) · `moj_db.py` (the parity twin) · `tests/test_moj.py` (1 allowed-set re-point) · `evaluate_unified.py` (2 version lines)
**Class:** 🟢 Gate-2 SIGNED (PO «نعم اوقع») — engine OUTPUT change, but VALUE-INVARIANT (the `trend.label` is a descriptive panel string; never feeds amount/low/high/method/leadership).

## 1. Why this matters
From the full-site DEBUG session (#5). `compute_trend` labelled a land trend «استقرار» (stability) at +0.3%/yr while the yearly medians swung ±45% (e.g. PIN 55010236: 6612→9688→9688→8700→5130→9688). The label keyed on the regression SLOPE only and ignored DISPERSION — so a flat-but-volatile series read as «stable». This contradicts the engine's own honesty ethos (Rule E23: a near-zero direction ≠ low spread).

## 2. Root cause
[moj_reference.py:298-303](moj_reference.py:298) (and the parity twin [moj_db.py](moj_db.py)) classified the slope into ارتفاع / انخفاض / استقرار with no dispersion check on the yearly medians.

## 3. What this patch does
In the `else` («استقرار») branch, compute the peak-to-trough spread of the yearly medians and relabel «متذبذب» (volatile) when it exceeds the project's 0.30 dispersion convention:
```python
_med = sorted(y['median_ft'] for y in years_data); _mid = _med[len(_med)//2]
_spread = (_med[-1]-_med[0]) / _mid if _mid else 0
label = 'متذبذب' if _spread > 0.30 else 'استقرار'
```
Applied identically to `moj_reference.compute_trend` (the LIVE report path — `evaluate_property.py:60` imports it) and `moj_db.py`'s "faster equivalent" (parity). ارتفاع / انخفاض unchanged. The frontend renders `trend.label` as text → «متذبذب» needs no UI change (neutral colour, slope≈0).

## 4. Scope boundary
The trend panel is descriptive. No value/range/method/leadership change. The SIGNED a3/T1.2 design (keep the qualitative label when the numeric slope is suppressed-for-staleness) is UNTOUCHED — this only adds dispersion-awareness to the label classification itself.

## 5. Verification — empirical evidence
- Functional (real `moj_reference.compute_trend`): volatile synthetic series → «متذبذب»; stable series (±<30%) → «استقرار»; clear up/down → ارتفاع/انخفاض.
- `tests/test_moj.py` allowed-set re-point (+«متذبذب»).
- DoD: aggregator + security + surface + broad walk (see Session_Log §20.94).

## 6. Deployment
```
git add "deploy v2/moj_reference.py" "deploy v2/moj_db.py" "deploy v2/tests/test_moj.py" "deploy v2/evaluate_unified.py" "deploy v2/CHANGELOG_v146.md"
git commit -m "Sprint 2.22.0b.65: trend dispersion-aware label (DEBUG #5) — «متذبذب» on flat-but-volatile data; value-invariant"
git subtree push --prefix "deploy v2" heroku master
git push origin master
```

## 7. Verification curl
```
curl -s https://thammen.qa/api/health   # → engine_version thammen-sprint2p22p0b65-trend-dispersion-label
```
A volatile-area land eval returns `trend.label` = «متذبذب»; a stable area stays «استقرار»; the 5-fixture value byte-gate identical to v236.

## 8. What's NOT in this patch
- The slope-suppressed-when-stale design (a3/T1.2) — intentionally unchanged.
- The threshold (0.30 full peak-to-trough) is the project's dispersion convention; tuning is a future calibration call.
- DEBUG #2 (BUA-unify) + #3 (E26 age-consistency) — the next signed sprint (b66).

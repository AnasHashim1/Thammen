# CHANGELOG v66 — Sprint 2.22.0a.14 (vi): bracket honest-range + window disclosure

**Engine:** `thammen-sprint2p22p0a14-bracket-honest-range` · api-health `3.1.0-sprint2.22.0a.14`
**Date:** 2026-06-01 · **Presentation/copy only — NO method/value change** (Gate-2 copy for (b)'s wording, Anas-signed).
**Files:** `moj_reference.py` (additive `ppm2_dispersion_36`), `evaluate_property.py` (thread 2 MoJValuation
fields), `evaluate_unified.py` (gate branch + Case-1 carry + version), new `test_sprint_2p22p0a14_bracket_honest_range.py`.
**Follow-up to a13 (CHANGELOG_v65):** closes **R10** + **CHECK-3-live**.

## 1. Why
a13's thin-cell credibility moved cells onto the bracket-success path, which had **no dispersion gate**.
Measured: **20 of 37** reliable villa bracket cells are dispersed (ppm² ≥0.30) = **7 a13-rescued (R10) +
13 PRE-EXISTING** always-reliable cells — all presenting as clean `comparison_bracket` reliable points
with no honest-range. Separately (CHECK-3-live): the bracket-success `source_ar` disclosed **no window
for any villa cell** (Abu Hamour "وسيط 37 معاملة…", 37 spanning ≤36mo). The bracket-success surface was
the only one missing BOTH the dispersion range and the window basis.

## 2. What (backend only; same pool, same median — NO value change)
- **(a) honest-range:** `_stage1_dispersion_gate` ([evaluate_unified.py:4121](evaluate_unified.py:4121))
  extended with a `comparison_bracket` branch gating on the cell's **36mo ppm² dispersion** vs
  `STAGE1_DISPERSION_T=0.30`. **The existing a10 application block reuses UNCHANGED**
  (`range_is_headline` + central_estimate + AR/EN disclosure + accuracy→`🟡 شواهد محدودة` + MUC `high`).
  `moj_reference.build_reference` adds additive `ppm2_dispersion_36`; `apply_moj_strategy` threads
  `bracket_ppm2_dispersion` (villa, cred only — `n24≥5`); `_select_primary_comparison` Case 1 carries it.
- **(b) window disclosure** (fires only when n is a 36mo count): headline `source_ar` appends
  **« (نافذة 36 شهراً) »**; the "Methodology Applied" brief `window` field
  ([output_briefs.py:852](output_briefs.py:852), previously unpopulated) lights up with the recent/total
  split **«{n36} معاملة، منها {n24} خلال 24 شهراً»**. Pure-24mo cells: `source_ar` **unchanged** (exception flagged, norm not annotated).
- **No median/value change** — the gate is presentation-only; a13's blend is untouched.

## 3. Scope (signed) + boundary
- **All 20 dispersed reliable cells gated** (7 rescued + 13 pre-existing) — the gate fires on dispersion,
  not cell-history; gating 7 and leaving 13 equally-dispersed would be incoherent and need extra
  rescue-origin tracking. **R10 generalized:** "bracket path had no dispersion gate; 20 dispersed reliable
  villa cells." **Anchors NOT gated:** Abu Hamour 0.208, Marikh 0.197 < 0.30.
- **Knife-edge flagged:** 3 cells within ±0.006 of T=0.30 (الثمامة 50 0.294 below; نعيجة 44 0.302 +
  ام عبيرية 0.305 above) — could flip on a data refresh. T=0.30 is the same threshold a10 already uses
  (no new calibration).

## 4. Verification — empirical (local, real functions, E14)
- **Isolated** `test_sprint_2p22p0a14_bracket_honest_range.py`: **19/19** (gate fires on dispersed bracket;
  anchor-clean 0.208 NOT gated; boundary 0.305 gated; `<5` floor → no thread; widened regression intact;
  window suffix + split string; end-to-end gate via the carried dispersion).
- **End-to-end live** (real `build_reference`→`apply_moj_strategy`→gate): Abu Hamour disp **0.208 → NOT
  gated** + window «37 معاملة، منها 28 خلال 24 شهراً»; الغرافة 600-900 **0.428 → gated**; العب **0.632 →
  gated**; الخريطيات 600-900 (pre-existing) **0.445 → gated**; Marikh 0.197 → not gated.
- **DoD:** aggregator **392/392** · security **15/15** · surface **45/45** · broad **57/57** (+1 new test). py_compile 3/3.

## 5. Deployment (Gate-1 — pending explicit Anas approval)
```
cd /d "C:\Thammen\deploy v2"
git subtree push --prefix "deploy v2" heroku master
git push origin master
```

## 6. Post-deploy verification (Rule #52)
Live smoke (Anas — POST is 403 from the dev container): a **dispersed reliable** villa cell (e.g. a
600-900 villa in الغرافة/الخريطيات) now shows `range_is_headline` + `🟡 شواهد محدودة` tier + MUC `high`
+ the window in `source_ar`/Methodology; **Abu Hamour 56/565/21 = 2.4M unchanged** but now with «نافذة 36
شهراً» disclosed; Marikh unchanged. `/api/health` engine = `…-bracket-honest-range`.

## 7. What's NOT in this patch
No value/method change (median untouched) · R7 built-type/**condition** axis (Branch B / 2.22.0b) ·
A16 alias-merge (R9, own sprint) · LAND bracket path (villa-only) · index.html (backend-only, like a10).

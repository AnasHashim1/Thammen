# CHANGELOG v73 — Sprint 2.22.0a.21 (B-1): land-floor / HBU decomposition + condition surfacing

**Engine:** `thammen-sprint2p22p0a21-land-floor-hbu-decomposition` · **SPRINT_TAG** `2.22.0a.21` ·
**api/health** `3.1.0-sprint2.22.0a.21` · **date** 2026-06-04
**Files changed:** `evaluate_unified.py` (helper + constants + attach + version) · `index.html`
(render) · `test_sprint_2_22_0a21.py` (new, 33 checks) · `CHANGELOG_v73.md`
**Class:** presentation / disclosure — **VALUE-INVARIANT** (Gate-2, signed brief
`docs/BRIEF_SprintB1_land_floor_decomposition.md`; Phase-0 §5 `docs/PHASE0_SprintB_condition_axis.md`;
multi-AI #54 GPT-5 + Gemini convergent, copy LOCKED).

---

## 1. Why this matters
On every villa comparison path the engine is **built-type / age / condition blind** (RISK_REGISTER
**R7**, bidirectional): it returns the comp pool's central tendency. For old-stock it **over-anchors** —
56/647/6 (V001 Maamoura) returns **3.8M**, which equals a ~5-year **market-rejected ask**; the real
clearing signal is land (~2.46M) + a modest premium. Phase-0 **F1** found the engine ALREADY computes a
land floor but **suppresses** it (Patch C) exactly in the **land-priced / old-stock cohort** (~10% of
valued villa cells, **0%** of reliable — all large-plot old-stock) — the case that needs it most. B-1
surfaces the land floor (an analytical Highest-and-Best-Use decomposition, VPS 2 / IVS 102) + the
implied-building residual + a land-anchored disclosure, next to the live a17/a19 condition caveat.

## 2. Root cause
- `_decompose_value` (`evaluate_unified.py:1204`, Sprint 2.18.1.1 Patch C) returns **None for the whole
  block** when `land_value > valuation_amount` (anti-negative-building guard). Correct for the compound
  bug it was built for (51/835/17), but it ALSO hides the legitimate land floor for ordinary land-priced
  villas (e.g. 55/296/13: المعراض land 2,547/m² × 1050 = 2,674,350 > 2,600,000 → block suppressed).
- The land floor that IS surfaced lives at `valuation.value_decomposition.land.estimated_qar`; the
  proposer's "None" was a wrong-field-path (a `cost`-keyed `land_value`, legitimately None for villas).

## 3. What this patch does
**Backend (`evaluate_unified.py`):**
- New villa-scoped helper `_villa_value_floor(amount, plot, moj_ref, existing_decomp)` →
  `{land_floor, land_per_m2_qar, land_n_transactions, window_months, reliable, implied_building_value,
  land_anchored, citation_ar/en, land_floor_note_ar/en, implied_building_note_ar/en,
  land_anchored_note_ar/en}` or None. **F2-prefer:** reuse `value_decomposition.land.estimated_qar` when
  present; **F1-fallback:** recompute `land_ppm² × plot` from the SAME `moj_reference` land category —
  **INDEPENDENT of Patch C** (so it surfaces when `land ≥ value`). `implied_building_value =
  max(amount − land_floor, 0)` (NEVER negative); `land_anchored = land_floor ≥ amount` → swaps the
  implied-building line for the land-anchored disclosure. **Never alters `amount`; never touches the
  Patch-C guard.**
- Attached at the decomposition site (post-`_build_unified_output`, where `value_decomposition` + `moj_ref`
  exist) under the **a17/a19 gate** (`_condition_note_applies` ⇒ villa/house + the 5 value-bearing
  comparison methods + amount + not dispersion-gated), in a swallowed try → never breaks evaluate. The
  block is set on `valuation.value_floor` + injected into the brief MU section (`_inject_value_floor_into_brief`).
  **Rule #39 deviation** vs the brief's literal "same a14 try-block": the a14 block runs INSIDE
  `_build_unified_output`, before `value_decomposition` is attached — co-locating with the decomposition
  enables the F2-prefer-then-F1-fallback the brief specifies; same JSON surface, same gate, same
  error-swallow, value-invariant.
- Copy = multi-AI LOCKED constants (verbatim AR + EN); AR numbers LRM-wrapped (U+200E, Operational #25).
- `ENGINE_VERSION` / `SPRINT_TAG` → a21. `api.py` UNTOUCHED (version auto-derives).

**Frontend (`index.html`):** a muted `.rn` block (the a17-proven class) directly under the range —
`land_floor_note` then either `implied_building_note` (positive) or `land_anchored_note` (floor ≥ value).

## 4. Verification — empirical evidence
- **Isolated `test_sprint_2_22_0a21.py` = 33/33** (production functions, E14): F2 56/647/6 (floor
  **2,456,736** / implied **1,343,264** / anchored False); **F1 55/296/13 (floor 2,674,350 / implied 0 /
  anchored True — LOAD-BEARING)**; F1 56/650/4 (1,413,000 / 1,887,000); F2-prefer-over-recompute; guards
  (amount/plot None, n<3, no-land → None); value-invariance (no amount key; implied = amount − floor);
  gate fires villa-thin/bracket/house, excludes dispersed-gated/apt/land; verbatim LOCKED copy; no-Latin
  in the 3 AR notes; citation present.
- **DoD matrix:** aggregator **392** · security **15/15** · surface-honesty **45/45** · broad auto-walk
  **64/64** (was 63; +1 new test; genuine clean pass 127.6s, zero failures, **no GIS flake**).
- **R14 (executed, not reasoned):** `node` absent → real Chromium (Claude_Preview): the served
  `index.html` loaded with **all inline functions defined + zero console errors** (whole-file JS syntax
  PASS incl. the new block); at **390×844** the value_floor block measured `scrollW==clientW`, block
  right-edge **350 < 390**, `overflowX=false` (no overflow).
- **Local E2E** (helper): floor matches the live `value_decomposition.land` byte-for-byte (Maamoura
  3,768 → 2,456,736).

## 5. Deployment
```
cd /d "C:\Thammen\deploy v2"
git add evaluate_unified.py index.html test_sprint_2_22_0a21.py CHANGELOG_v73.md docs/
git commit -m "Sprint 2.22.0a.21 (B-1): land-floor / HBU decomposition + condition surfacing (value-invariant)"
git subtree push --prefix "deploy v2" heroku master
git push origin master
```

## 6. Verification curl (post-deploy, browser-UA per #61)
```
curl -s -X POST https://thammen.qa/api/evaluate -H "Content-Type: application/json" ^
  -A "Mozilla/5.0 ... Chrome/120 Safari/537.36" -d "{\"zone\":56,\"street\":647,\"building\":6}" > out.json
findstr /C:"value_floor" out.json
findstr /C:"land_anchored" out.json
```
Expect (ZERO value drift): 56/565/21 = 2.4M + block · 54/541/6 = 5.4M + block · 52/903/90 = refusal (no
block) · 55/296/13 = 2.6M + floor 2.67M + `land_anchored:true` · 56/647/6 = 3.8M + floor 2.46M + implied
~1.34M.

## 7. What's NOT in this patch (scope boundary)
- Any **calibrated** condition/age **adjustment** (→ B-2 / 2.22.0b Stage-2 user input). Age
  auto-detection. **Land-path** changes (villa-only). The dispersion-**gated** pools keep their a10/a14
  honest-range (value_floor rides the same `_condition_note_applies` gate → excluded there by design).
- `stock_strata.compute_land_median` a18-alignment → **R15** (separate cleanup).
- The headline value, range, tier, MUC, method, or any refusal decision — all **byte-identical**.
- PDF-prominence flag (brief §7): confirm the Red Book / IVS clause + required disclosure prominence in a
  PDF lookup — **non-blocking** fast-follow.

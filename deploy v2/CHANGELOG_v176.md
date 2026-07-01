# CHANGELOG v176 — Sprint 2.22.0b.95 «شارة الفرز المبدئيّ» (م٢ — the preliminary-subdivision indicator)

**Engine:** `thammen-sprint2p22p0b95-subdivision-indicator` · **SPRINT_TAG** `2.22.0b.95` · api-health `3.1.0-sprint2.22.0b.95`
**Date:** 2026-07-02 · **Files:** `index.html` (the land-branch subdivision logic + `.thmr-sub` CSS) · `evaluate_unified.py` (2 version lines) · `test_sprint_2_22_0b95.py` (new)
**Class:** 🟢 FRONTEND-ONLY / **VALUE-INVARIANT** (display-only insight; never touches the number). **Gate-2:** the SIGNED report-redesign §6 (Gemini r3 ⭐⭐, the م٢ item) + the PO package «go» 2026-07-02.

## 1. What this patch does (`showShortReport`, land branch)
The SIGNED §6 subdivision rule, computed **conservatively from the already-broadcast b10 `plot_dims_m`** (no new GIS, no engine change):
- Gate: `plot_area >= 800` + a rectangular dims broadcast.
- **Corner plot:** its two street frontages ARE the two edge lengths (adjacent edges — fully decidable) → rule: both ≥ 12m; the division frontage = the longer edge.
- **Non-corner plot:** the street edge is ONE of the two dims but WHICH is unknown → we claim **only when even the shorter dim ≥ 24m** (whichever edge faces the street, the rule passes); **undecidable cases render NOTHING** (no semi-strong claim on a guess — the #54 honesty bar). Frontages are **never summed** (§6).
- `N = MIN(floor(area/400), floor(frontage/12))`, rendered at N≥2 as a green info line under the chips with the SIGNED cautious microcopy: «مؤشّرات الأرض تتيح الفرز مبدئياً إلى {قطعتين/N قطع} — يخضع لقوانين الارتدادات وموافقة التخطيط العمرانيّ بوزارة البلدية.» — Arabic dual/plural agreement (قطعتين / قطع / قطعة — the linguist persona) + the EN twin.

## 2. Deviation flag (#39)
The FULL م٢ spec called for a geometric frontage derivation (which edge faces which street, from the plot polygon + adjacent streets). That needs an engine-additive `edge_evidence` broadcast (a later slice). b95 ships the honest decidable subset TODAY: corner = fully decidable; non-corner = decidable when min(dims)≥24; everything else stays silent. **Nothing lost** — the silent cases would otherwise require guessing.

## 3. Value-invariance
Display-only; the only `v.amount` multiplications remain the 3 disclosed conventions (pinned). The 5-fixture value byte-gate is byte-identical by construction.

## 4. Verification — empirical
- Isolated `test_sprint_2_22_0b95.py` **16/16** (land-branch scope · the §6 gates · corner 12/12 · non-corner min≥24 conservative · no frontage summing · N formula · N≥2 · the SIGNED microcopy · dual/plural · placement · CSS · value-math pin · R6 format). Siblings b90 **29/29** · b94 **15/15**.
- DoD: aggregator **ALL COUNTS MATCH** · security **16/16** · surface **45/45** · **broad walk 151/151 ALL GREEN** (150→151, zero re-points).
- **R14 real-Chromium 375×812** (preview; DOM-measured): real land 502m² → NO line (area gate); corner 900m² 30×30 → «إلى قطعتين» ✓; non-corner 1000m² 20×50 → **silent** (undecidable — correct); non-corner 1200m² 25×48 → «قطعتين» ✓; corner 1000m² 10×60 → silent (frontage <12) ✓; 1700m² 40×42 → «3 قطع» ✓; villa → never; **EN** "…subdivision into 2 parcels…" ✓; no doc overflow; **0 console errors**.

## 5. Deployment
`git push origin master` (backup FIRST) → `git subtree push --prefix "deploy v2" heroku master` (backgrounded).

## 6. Verification curl (post-deploy)
`/api/health` → engine b95. Served `index.html`: `thmr-sub` + «الفرز مبدئياً» present. 5-fixture byte-gate identical.

## 7. What's NOT in this patch
- The engine-side frontage derivation (edge↔street mapping broadcast) — the fuller م٢ slice, unblocks the undecidable-non-corner cases.
- م٣ (bank PDF) — next in the queue.

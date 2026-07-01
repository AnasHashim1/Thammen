# CHANGELOG v174 — Sprint 2.22.0b.93 «الفخامة + مرآة الحاضنة» (luxury hero chrome + result-screen tiers mirror)

**Engine:** `thammen-sprint2p22p0b93-lux-hero-tiers-mirror` · **SPRINT_TAG** `2.22.0b.93` · api-health `3.1.0-sprint2.22.0b.93`
**Date:** 2026-07-02 · **Files:** `index.html` (luxury CSS + the rhero tiers mirror) · `evaluate_unified.py` (2 version lines) · `test_sprint_2_22_0b93.py` (new) · `test_sprint_2_22_0b92.py` (own version pin → R6-agnostic)
**Class:** 🟢 FRONTEND-ONLY / **VALUE-INVARIANT** (`api.py` + the valuation engine UNTOUCHED). **Gate-2** signed: the PO «go» 2026-07-02 package (Gemini r7 #3 + the b92 carried-forward).

## 1. What this patch does
- **Luxury hero chrome (Gemini r7 #3)** on BOTH navy heroes (`.rhero` result + `.thmr-hero.lux` short report — one نسق): (a) a **cadastral watermark** — a LOCAL data-URI SVG of abstract plot parcels at 4% opacity (zero CDN — the b45 lock holds); (b) a **champagne-gold hairline ring** (1px gradient border via the mask-composite technique) with a slow 9s sheen sweep; `prefers-reduced-motion` → animation off.
- **The b92 tiers mirror on the result screen:** the `.rhero` range bar had the SAME edge-pinned dot defect (`right:_hpct%`, b48). When skewed (<20/>80) it now renders the labeled tiered bracket (chip + 3-block track + «الأرضية السعرية»/«السقف السوقي» + the honest cost/geo legend); **the b48 rbar is KEPT VERBATIM** for the central case (pins survive — zero re-points).

## 2. Value-invariance
CSS + a display branch only; no `v.amount` arithmetic added (pinned by the isolated test); the 5-fixture value byte-gate is byte-identical by construction.

## 3. Verification — empirical
- Isolated `test_sprint_2_22_0b93.py` **15/15** (shared lux selectors · local data-URI watermark @.04 · gold ring + sheen + reduced-motion · the lux class on the SR hero · the rhero skew gate/clamp/labels/honest-legend · the rbar verbatim · no value-math · R6 version format). b92 re-run **22/22** (its own exact-version pin relaxed → R6-agnostic — self-caught).
- DoD: aggregator **ALL COUNTS MATCH** · security **16/16** · surface **45/45** · **broad walk 149/149 ALL GREEN** (148→149, zero re-points).
- **R14 real-Chromium 375×812** (preview, live fixtures; screenshot channel down — §20.34 — DOM/computed-style measurements are the channel): SR hero `lux` + watermark computed (`url("data:image/svg…`, opacity .04) + ring `animationName:luxsheen`; result rhero → tiers + chip «القيمة التقديرية» + the honest legend on cost-led (f_marikh ٢٬٤٠٠٬٠٠٠), watermark computed; the synthetic central case keeps the b48 `rbar` (no tiers); **no doc overflow (375==375)**; **0 console errors/warnings**; `node --check` both inline blocks OK.

## 4. Deployment
`git push origin master` (backup FIRST) → `git subtree push --prefix "deploy v2" heroku master` (Rule #43; backgrounded).

## 5. Verification curl (post-deploy)
`/api/health` → engine b93. Served `index.html`: `luxsheen` + `thmr-hero lux` + the rhero tiers branch present. 5-fixture value byte-gate byte-identical to b92.

## 6. What's NOT in this patch
- b94 (unknown-chips cleanup + the «ترقية دقّة المؤشّر» block) — next sprint of the signed package.
- The full-report cover card keeps its existing style (the luxury ring scoped to the NAVY heroes).

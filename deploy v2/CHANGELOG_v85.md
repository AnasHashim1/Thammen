# CHANGELOG v85 — Sprint 2.22.0b.4 (B-2): condition/value axis — teardown down-anchor + luxury-new premium

**Engine:** `thammen-sprint2p22p0b4-condition-value-axis` · **SPRINT_TAG** `2.22.0b.4` ·
**api/health** `3.1.0-sprint2.22.0b.4` · **Date:** 2026-06-07
**Files changed:** `evaluate_unified.py` (constants + injection + CLI + version) · `api.py` (condition docstring) ·
`index.html` (dropdown option + disclosure) · `test_sprint_2_22_0b4.py` (new, 15) · `test_sprint_2_22_0b3.py`
(R6 fix — version pin → format) · `CHANGELOG_v85.md`
**Class:** **METHODOLOGY — MOVES the headline value** (Gate-2). Two opt-in R7 levers, mutually exclusive:
**DOWN** `condition='teardown'` → land − demolition; **UP** `is_luxury + new` → Cost-Approach (DRC) value `land + BUA×construction`
toward the confirmed-sale GT. **Value-invariant on every other input** (4 anchors byte-identical). Briefs:
`docs/BRIEF_SprintB2a_teardown_down_anchor.md` (teardown, signed «assume and proceed») + §20.27 (luxury-new,
PARK unlocked by Anas 2026-06-07 «we have all the info we need»). First R7-axis sprint that **SOLVES** (not just
discloses) — **both extremes**, data-ready.

---

## 1. Why this matters

A live 20-combination sensitivity matrix on 56/565/21 (v170) proved the engine is **blind to condition AND
finish** — `new = good = maintenance = renovated = luxury = 2,400,000` exactly — bidirectional R7. It both
**over-values the dilapidated case ~+35%** (`age30 + maintenance + 1 floor = 2.30M` while the land floor is
~1.70M and the building is a demolition **liability**) AND **under-values the premium new-build case ~−40%**
(V002/V003 — new luxury villas SOLD **4.0M** on this very street, engine 2.4M). This sprint fixes **both ends**:
a teardown DOWN-anchor + a luxury-new UP-premium.

## 2. Root cause

The Qatar 10-Year Rule (`_age_aware_substantiality_multiplier`, `evaluate_unified.py:906`) **suppresses** the
BUA-substantiality uplift (adj→0) for any villa ≥10y — but it **never SUBTRACTS toward land**. So a teardown
subject stays pinned at the comparison median (which assumes a sound building). No path re-anchors downward.

## 3. What this patch does

- New `condition='teardown'` (AR label «آيل للسقوط / يجب هدمه»). When stated, on a **villa/house** with a real
  amount: `value = land_floor − demolition`, reusing the shipped `_villa_value_floor` (land floor, n≥20).
- `DEMO_QAR_PER_M2 = 240` × BUA **clamped to [100k, 150k]** (fallback `plot × 0.55` when no floors input).
  **PO-calibrated (Anas, Qatar market, Rule #7):** demolition is roughly FLAT in a 100k-150k band, NOT linear
  with size — a SMALL villa ≈ 100k (floor), a MID villa ≈ 120k, a LARGE villa caps at 150k. (240/m² yields the
  120k mid-point; the clamp enforces the small/large ends.) (The first web-derived 60/m² — US demo $4-7/sqft ÷
  GCC labour — captured LABOUR ONLY and missed debris haulage + municipality fees + site clearance.) Single
  tunable set (like D5/D6); at 100-150k, demolition is ~6-9% of the land floor.
- Headline = `_r100k(land_floor − demolition)`; range `[central×0.88, land_floor]` (downward); `material_
  uncertainty.level → high`; `valuation.teardown{land_floor, demolition_cost, per_m2, bua, note_ar/en}`.
- `index.html`: the «آيل للسقوط / يجب هدمه» option + a muted `--warn` 🏚️ disclosure («HBU = redevelopment:
  land − demolition; the standing building is a liability»).
- **Opt-in ONLY**: fires solely on `condition='teardown'`; never auto-detected (E17 — broker states, engine
  values); villa/house only (raw_land/apartment/compound skip); the other condition values UNCHANGED.
- **B-2b luxury-new premium via Cost Approach / DRC (UP lever, §20.27 PARK + §20.9 DRC unlocked).** When the
  user states `is_luxury` AND new (`condition='new'` or `building_age_years<5`), a premium new-build villa is
  valued by the **Cost Approach**: `value = land_floor + BUA × construction_cost`. BUA uses **FULL zone
  coverage** (a luxury villa builds to the ceiling, NOT b1's conservative ×0.8) + the **penthouse rule** as an EXPLICIT
  «بنتهاوس» dropdown input: `BUA = footprint × (floors + 0.5×penthouse)`. Default for a luxury new-build is
  ground+first+penthouse (×2.5 = V002/V003), but the user can drop the penthouse (×2.0 → 3.6M, correcting the
  over-assumption) or add floors (fl3+PH = ×3.5 → 5.0M). A user-supplied footprint wins. `construction_cost = 3500
  QAR/m²` **calibrated on V002/V003** (building value 2.3M / BUA ~657 m²). `material_uncertainty → high` + a
  `luxury_new_premium{method:'cost_approach_drc', land_floor, building_value, bua_m2, construction_qar_per_m2,
  note}` block + a 💎 disclosure. Mutually exclusive with teardown; opt-in; villa/house. The DRC **scales with
  the actual building** (footprint × construction) — far better than a flat % — and matches the V002/V003 GT
  (4.06M ≈ 4.0M, ~1.5%). The verification revealed b1's suggested footprint (×0.8 cap) understates a luxury
  build, hence the FULL-coverage choice here.

## 4. Verification — empirical evidence

- py_compile (evaluate_unified + api) OK.
- **Local E2E on the REAL engine (live GIS) — 56/565/21, the full R7 axis (both levers + invariance):**
  | input | amount | range | |
  |---|---|---|---|
  | good / new-only / luxury-only / luxury+maintenance | 2,400,000 | 2.2–2.6M | **byte-identical** — each lever needs the exact opt-in |
  | **teardown** (no floors) | **1,600,000** | 1.4–1.7M | **DOWN −33%**: land 1,700,100 − demo (100k floor; 150k cap at 2-3 floors) |
  | **luxury + new** (default G+1+PH) | **4,100,000** | 3.5–4.4M | **UP (DRC)**: land 1.70M + BUA 675m² (fp×2.5) × 3500 → **matches V002/V003 (4.0M)** |
  | luxury + new, **NO penthouse** | 3,600,000 | — | the «بنتهاوس» option drops BUA to 540 (fp×2.0) — corrects the over-assumption |
  | luxury + new, floors 3 + penthouse | 5,000,000 | — | DRC scales: BUA 945 (fp×3.5) |
- Isolated `test_sprint_2_22_0b4.py` **15/15** (production constants + `_villa_value_floor` reuse [E14] +
  teardown math + index surfaces + version).
- **DoD:** aggregator **392** · security **15** · surface-honesty **45** · broad **73/73** (72→73, clean, 104s).
- **R14 real-Chromium 390×844** (node absent): **0 console errors**; «آيل للسقوط / يجب هدمه» in the condition
  dropdown; teardown payload renders headline «١٬٥٠٠٬٠٠٠ – ١٬٧٠٠٬٠٠٠ ر.ق» (range-as-lead) + median marker
  «الوسيط ≈ ١٬٧٠٠٬٠٠٠» + the 🏚️ «إعادة التطوير / عبئاً» disclosure; no horizontal overflow (docW 390).
- **R6 self-catch:** `test_sprint_2_22_0b3.py` carried an EXACT version pin (`=b3`) that the b4 bump broke
  (broad 1-fail); fixed both b3 + b4 to **version-agnostic format** checks (Lesson-2 / R6).

## 5. Deployment

```
cd /d "C:\Thammen\deploy v2"
git add evaluate_unified.py api.py index.html test_sprint_2_22_0b4.py test_sprint_2_22_0b3.py CHANGELOG_v85.md docs/BRIEF_SprintB2a_teardown_down_anchor.md
git commit -m "Sprint 2.22.0b.4 (B-2a): teardown down-anchor [BUILT, DoD-green, R14-pass, HELD at Gate-1]"
git push origin master
git subtree push --prefix "deploy v2" heroku master    # Gate-1 — explicit Anas consent ONLY
```

## 6. Verification curl (post-deploy)

```
curl -s https://thammen.qa/api/health    # expect 3.1.0-sprint2.22.0b.4
# 4 standard anchors BYTE-IDENTICAL (teardown is opt-in):
#   56/565/21 → 2.4M · 54/541/6 → 5.4M · 55/296/13 → 2.6M · 52/903/90 → refusal
# teardown hit:
curl -s -A "Mozilla/5.0 ... Chrome/120 Safari/537.36" -X POST https://thammen.qa/api/evaluate/details \
  -H "Content-Type: application/json" -d "{\"zone\":56,\"street\":565,\"building\":21,\"condition\":\"teardown\"}"
# expect: valuation.amount ≈ 1,700,000 (land − demolition), valuation.teardown.applied=true
```

## 7. What's NOT in this patch (scope boundary)

- **Calibrated Lever-2 band** (ordinary old villa +0–10% re-anchor) — **PARKED n≥20** (§20.27).
- **Lever-1** (luxury/finish premium UP) — **PARKED n≥20**. So ordinary `good`/`maintenance`/`luxury` still
  do NOT move the headline (by design — they need the GT-2 corpus).
- **No auto-detection** of teardown (user-stated only).
- `poor`/`fair` get NO down-anchor (caveat-only; the partial re-anchor IS the calibrated band).
- The demolition model (`DEMO_QAR_PER_M2 = 240` clamped to [`DEMO_FLOOR_QAR`=100k, `DEMO_CAP_QAR`=150k]) is
  **PO-calibrated** (Anas, Qatar market: small 100k / mid 120k / large 150k) — a tunable set; adjust if the
  market moves.

# CHANGELOG v85 — Sprint 2.22.0b.4 (B-2a): teardown / demolition down-anchor

**Engine:** `thammen-sprint2p22p0b4-teardown-down-anchor` · **SPRINT_TAG** `2.22.0b.4` ·
**api/health** `3.1.0-sprint2.22.0b.4` · **Date:** 2026-06-07
**Files changed:** `evaluate_unified.py` (constants + injection + CLI + version) · `api.py` (condition docstring) ·
`index.html` (dropdown option + disclosure) · `test_sprint_2_22_0b4.py` (new, 15) · `test_sprint_2_22_0b3.py`
(R6 fix — version pin → format) · `CHANGELOG_v85.md`
**Class:** **METHODOLOGY — MOVES the headline value** on a teardown villa (Gate-2). Opt-in only
(`condition='teardown'`); **value-invariant on every other condition** (4 anchors byte-identical). Brief
`docs/BRIEF_SprintB2a_teardown_down_anchor.md` (Gate-2 signed by Anas «assume and proceed» + the due-diligence
mandate). First R7-axis sprint that **SOLVES** (not just discloses) — the data-ready teardown extreme of B-2.

---

## 1. Why this matters

A live 20-combination sensitivity matrix on 56/565/21 (v170) proved the engine is **blind to condition** —
`new = good = maintenance = renovated = 2,400,000` exactly — and **over-values the dilapidated case ~+35%**:
`age30 + maintenance + 1 floor = 2.30M` while the land floor is ~1.70M and the building should be a demolition
**liability**, not +0.6M of implied value. A villa the buyer intends to demolish was priced as a sound
standing home.

## 2. Root cause

The Qatar 10-Year Rule (`_age_aware_substantiality_multiplier`, `evaluate_unified.py:906`) **suppresses** the
BUA-substantiality uplift (adj→0) for any villa ≥10y — but it **never SUBTRACTS toward land**. So a teardown
subject stays pinned at the comparison median (which assumes a sound building). No path re-anchors downward.

## 3. What this patch does

- New `condition='teardown'` (AR label «آيل للسقوط / يجب هدمه»). When stated, on a **villa/house** with a real
  amount: `value = land_floor − demolition`, reusing the shipped `_villa_value_floor` (land floor, n≥20).
- `DEMO_QAR_PER_M2 = 200` × BUA (fallback `plot × 0.55` when no floors input). **PO-calibrated (Anas, Qatar
  market, Rule #7):** a mid-size villa (~500 m² BUA) demolishes for ~100,000 QAR → ~200/m², scaling with size.
  (The first web-derived 60/m² — US demo $4-7/sqft ÷ GCC labour — captured LABOUR ONLY and missed debris
  haulage + municipality fees + site clearance; the PO's real-market number wins.) Single tunable constant
  (like D5/D6); demolition is ~6% of the land floor, so the exact value barely moves the headline.
- Headline = `_r100k(land_floor − demolition)`; range `[central×0.88, land_floor]` (downward); `material_
  uncertainty.level → high`; `valuation.teardown{land_floor, demolition_cost, per_m2, bua, note_ar/en}`.
- `index.html`: the «آيل للسقوط / يجب هدمه» option + a muted `--warn` 🏚️ disclosure («HBU = redevelopment:
  land − demolition; the standing building is a liability»).
- **Opt-in ONLY**: fires solely on `condition='teardown'`; never auto-detected (E17 — broker states, engine
  values); villa/house only (raw_land/apartment/compound skip); the other 4 condition values UNCHANGED.

## 4. Verification — empirical evidence

- py_compile (evaluate_unified + api) OK.
- **Local E2E on the REAL engine (live GIS) — 56/565/21 before/after (DEMO=200/m²):**
  | condition | amount | range | demo | |
  |---|---|---|---|---|
  | good | 2,400,000 | 2.2–2.6M | — | byte-identical |
  | maintenance | 2,400,000 | 2.2–2.6M | — | byte-identical (ordinary condition still doesn't move — by design) |
  | **teardown** (no floors) | **1,700,000** | **1.5–1.7M** | 49,500 (BUA 248) | **−29% re-anchor** to land 1,700,100 − demo |
  | teardown + 2 floors | 1,600,000 | 1.4–1.7M | 149,800 (BUA 749) | demolition **scales with size** (mid-villa ≈ 100k) |
  | teardown + 3 floors | 1,500,000 | 1.3–1.7M | 218,600 (BUA 1093) | larger villa → larger demo → lower value |
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
- The demolition number `DEMO_QAR_PER_M2 = 200` is **PO-calibrated** (Anas, Qatar market: ~100k for a mid-size
  villa) — a single tunable constant; adjust if the market moves.

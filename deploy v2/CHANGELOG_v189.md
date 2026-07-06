# CHANGELOG v189 — Sprint 2.22.0b.108 «توحيد قسم الافتراضات في صفحة واحدة بالتقرير» (S3 — the assumptions register)

**Engine:** `thammen-sprint2p22p0b108-assumptions-register` · **SPRINT_TAG** `2.22.0b.108`
**Date:** 2026-07-06 · **Files:** `index.html`, `evaluate_unified.py` (the 2 version lines) (+ `test_sprint_2_22_0b108.py`)
**Class:** 🟢 FRONTEND copy / VALUE-INVARIANT — one numbered annex in `showReport` (the FULL report, Layer 3) +
an actionable floors nudge on the cost row; no value/method/rule change (the 5-fixture villa byte-gate holds
by construction). `api.py` untouched.

---

## 2. Why (RICS VPS 2 credibility: no unified assumptions register)

The RICS valuer-lens audit flagged that the report never stated its assumptions in one place. RICS VPS 2 /
IVS 102 require the valuation's assumptions and special assumptions to be disclosed. The engine already MAKES
these assumptions (condition-not-inspected, HBU-residential, the built-ratio 0.77, the floors default, the
50-yr straight-line depreciation, the RCN ladder, the E26 system-age basis) — S3 surfaces them in ONE VPS 2
register on the professional artifact, assembled mostly from **already-broadcast fields**.

## 3. What this patch does

A new **numbered annex «الافتراضات والافتراضات الخاصّة (RICS VPS 2 / IVS 102)»** in the full report (Layer 3),
placed after the property-basics section, inside the valued path:

**Standing assumptions (every valued report):**
- **Condition & finish** — an assumption; not inspected on site (references the detailed «حول العقار» note, not duplicated).
- **Use** — residential highest-and-best-use under the current zoning; no higher development potential assessed (HBU).
- **Evidence window** — registered sales up to 24 months (widening to 36 when thin), with no explicit time adjustment (cross-ref S1).

**Cost-led additions (gated `leader==='cost'`, read from `value_stack.cost`):**
- **C-3 BUA + built-ratio 0.77** — «مساحة البناء ≈ {bua_m2} = ground footprint × 0.77 × floors».
- **The FLOORS-default assumption (the PO's 56/565/21 case)** — «يُفترَض طابقان (أرضيّ + أوّل) ما لم تُدخِل عددها …» — **only when the floor count is not provided** (villa 21 = G+1+penthouse ≈ 2.5 floors is invisible to QARS → the default 2 understates the BUA).
- **C-2 RCN ladder** (shell 1,200 · ordinary 2,200 · good 2,500 · high 3,000 · luxury 3,500) + the applied finish level (read from `cost.finish`).
- **C-2 depreciation** — straight-line over a 50-year useful life combining physical/functional/economic obsolescence + the broadcast remaining-value ratio (`cost.retention`).
- **E26 age basis** — the system-documented (CGIS) age is the basis; a user actual age is a sensitivity, not the headline.
- **C-6 cost calibration** — n=1 (V001, within ±1%), restated concisely (b19 already carries this — verify-first, no duplication issue since this is the register's concise entry).

**Income-led addition (C-5):** the cap-rate source cell (district / bracket, net of costs) when income leads.

**+ an actionable floors nudge on the «تفكيك المرتكز» cost breakdown row** (cost-led + floors not provided) —
«يفترض هذا الرقم طابقين؛ … أدخِل عدد الطوابق في «حسّن التقييم» لتدقيق مرتكز الكلفة» — the prompt where the owner
reads the cost figure.

Bilingual (`t()`); RICS/IVS tokens LRM-wrapped; register-consistent with the b105 lock.

## 4. VALUE-INVARIANT

Pure disclosure of what the engine already assumed — constants (0.77, floors-default, 50-yr, the RCN ladder)
authored as static bilingual text + the broadcast numbers (bua_m2, retention, finish, cap_rate_provenance).
No figure/method/rule touched; `api.py` + the engine logic untouched (only the 2 version lines). R14: Marikh
amount **2,400,000**, income **2,800,000**, market **2,400,000** — all unchanged.

## 5. Verification (measured)

- Isolated `test_sprint_2_22_0b108.py` **20/20** (header · 3 standing · cost-gated BUA/floors/RCN/depr/E26/calib
  · income cap-rate · the floors nudge · placement inside hasValuation after property-basics) · py_compile OK ·
  `node --check` OK.
- DoD: aggregator **395/395 MATCH** · security **16/16** · surface-honesty **45/45** · broad walk **163/163
  ALL GREEN** — **ZERO re-points** (a new additive annex pins no prior string).
- **R14 real preview 390×844** (DOM-measured, AR + EN):
  - **cost-led (Marikh):** full register renders (all standing + all cost additions, RCN «عاديّ» = the ordinary finish, V001 calibration) + the floors nudge; amount **٢٬٤٠٠٬٠٠٠** unchanged; no overflow.
  - **market-led (Abu Hamour):** register present with the 3 standing lines only, **no BUA/floors additions** (correctly cost-scoped); amount **٢٬٤٠٠٬٠٠٠**.
  - **income-led:** register + cap-rate line; amount 2,800,000.
  - **EN:** all lines + the nudge in English, no AR leak, `dir=ltr`, no overflow; **0 console errors**.
- **Personas:** lawyer APPROVE (a VPS 2 requirement fulfilled — transparent disclosure raises defensibility;
  the floors-default + nudge is honest about a known QARS limitation; no elevated claim) · linguist APPROVE
  (register-consistent with the b105 lock; precise RCN ladder; accurate EN twins).

## 6. Deployment

- `git push origin master` FIRST, then `git subtree push --prefix "deploy v2" heroku master` (§20.112).
- **NOT yet deployed** — local build (PO: «أكمل البناء محلياً»).

## 7. Verification curl (post-deploy)

- `/api/health` → `3.1.0-sprint2.22.0b.108`.
- served `index.html`: «الافتراضات والافتراضات الخاصّة (&lrm;RICS VPS 2 / IVS 102&lrm;)» present ·
  «يُفترَض طابقان (أرضيّ + أوّل)» present · «net-to-gross ratio of 0.77» present.
- the 5-fixture villa byte-gate byte-identical to v275 (browser-UA #61).

## 8. What's NOT in this patch

- The backend `value_stack.cost.assumptions_en` twin is still None (the §20.113 EN residue) — the register
  authors its own bilingual text so EN users are covered here; the bare `assumptions_ar` twin remains for a
  later backend `_en` pass. The land geo-filter = **S4 (b109)**, Gate-2. The trend filter = **S5 (b110)**.
  The condition modal (the number adapts to condition) = **S7 (b111)**, Gate-2, signed brief first.

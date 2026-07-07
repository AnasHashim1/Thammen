# CHANGELOG v193 — Sprint 2.22.0b.113 «الجوهر / B-2 — نافذة حالة العقار: الرقم يتكيّف مع الحالة» (condition-axis / opt-in stratum lead)

**Engine:** `thammen-sprint2p22p0b113-condition-stratum-lead` · **SPRINT_TAG** `2.22.0b.113`
**Date:** 2026-07-07 · **Files:** `evaluate_unified.py` (S7 constants + `_condition_stratum_lead` helper + the cost_led if/else wiring + 5 leadership fields + 2 version lines), `index.html` (refine friction note + the short-report honesty overrides) (+ `test_sprint_2_22_0b113.py`; 1 R6 re-point b104)
**Class:** 🔴 **Gate-2 VALUE-AFFECTING on the cost-led villa path — GUARDED / OPT-IN.** The blind default (no user condition attestation) is **BYTE-IDENTICAL** (the 5-fixture villa gate holds — only a positive attestation moves the number). PO-SIGNED brief («لنبنيه وقع»). `api.py` untouched.
**Deploy:** 🚫 **NOT deployed — local build.** Gate-2 discipline: the opt-in blast-radius table (`docs/GATE2_b113_condition_axis_optin.md`) awaits the PO's sign-off before the Heroku push (same gate as S4/b109).

---

## 2. Why (the r9 finding, PO-signed direction)

The cost floor (DRC) structurally **under-prices a functional villa** in an appreciating land market. On Marikh (54/541/6, 17yr, condition unknown) the engine leads with the conservative **cost floor 2,400,000**, while the RELIABLE market strata it already computes say: land-priced 2.25M · **modern (price-position «الشريحة المتوسّطة سعراً», n=11, reliable) ≈ 3.4M** · luxury («الشريحة الأعلى سعراً», n=15, reliable) ≈ 5.3M. A normal maintained 17yr villa ≈ the modern stratum — **a reliable market number the engine owns but does not lead with, because condition is unknown so it stays conservative.**

S7 lets the OWNER supply the missing signal: on a **positive condition attestation** (via the refine screen), a cost-led villa **leads with the matching reliable price-position stratum** (indicative, disclosed) instead of the cost floor. Blind (no attestation) → the conservative floor stays. This is the documented R7 under-anchor fix (§20.10.2 «defensible ~2.5–2.8M with condition»), shipped as an **opt-in the owner controls**, not an automatic lift.

## 3. What this patch does

### 3.1 Engine — `_condition_stratum_lead(condition, is_luxury, plot_area_m2, stock_strata, cost_floor)` (new pure helper)
Returns `{stratum, value, n, median_per_m2, label_ar, label_en}` or `None`. Guards (all non-negotiable, brief §4):
- **Positive attestation only** — `condition ∈ {good, renovated, new, excellent, very-good}`. `teardown`/`maintenance`/`average`/`None`/`''` → `None` (the floor keeps the lead; **the E25/R7 rail — cost is a floor, never chased up**).
- **finish → stratum:** `is_luxury` truthy → `luxury_new` («الشريحة الأعلى سعراً»); else → `modern_stock` («الشريحة المتوسّطة سعراً»). The b100 **price-position** labels (Gemini C3, #54: NOT «حديثة» — a maintained 17yr villa is «مُصانة», not «حديثة»; the internal stratum name stays internal).
- **reliable only** — the matching stratum must be `reliable` with **n≥10**; else `None`.
- **never below the floor** — `value = median_per_m2 × plot` must be `≥ cost_floor`; else `None` (the number can only be lifted, never lowered, by the opt-in).
- **cost_led only** — wired inside the b20 `cost_led` branch; every other leader (market/geo/e25/income/land/refusal) is untouched.

### 3.2 Engine — the cost_led block is now BRANCHED (`if _s7: … else: <existing block verbatim>`)
On a firing S7: `amount = _r100k(stratum value)`, `low = _r100k(cost floor)` (the floor is the honest low), `high = _r100k(max(stratum, prior market-muted high))`, `range_is_headline` popped, `leader='condition_stratum'` / `rule='condition_stratum_led'`, `+stratum`/`stratum_n`/`stratum_label_ar`/`stratum_label_en`/`cost_floor`, the disclosed **note_ar/en**, **MUC high**, and the **ISS-A07 recompute** of `value_decomposition` + `value_floor` on the new central (coherence — the b14/b67 discipline). The **else branch is the existing cost_led block byte-for-byte** → the blind default is byte-identical.

### 3.3 Frontend — the neutral opt-in friction note (refine screen «العمر والحالة» group)
«◆ حالتك تُغيّر الرقم: إقرارٌ إيجابيّ (جيدة/مُرمّم/جديد) قد يرفع التقدير إلى شريحة عقارك السوقيّة، وإقرارٌ أدنى قد يخفضه — والرقم يبقى **استرشاديّاً**. وأيّ عدم دقّةٍ في إقرارك تجعله غير صالحٍ عند الفحص الميدانيّ من البنوك أو المشترين.» — the **Gemini-C2 inspection-consequence friction** (an honest deterrent against over-claiming, NOT a «unlock your higher value» dark pattern — the r9 rejection). Bilingual (`t()`).

### 3.4 Frontend — short-report HONESTY overrides (gated on `condition_stratum_led` ONLY → every other short report byte-identical)
A condition-led number came from the owner's attested condition → the reliable stratum, **not** from matched sales. The market basisLn («N صفقة مطابقة لنوعك وعمرك، وسيطها مرجعك») + the cost-led «اطّلعنا عليها — ولم تقُد الرقم» proof rows would **both misstate the basis**. `_isCondLead` overrides:
- **basisLn** → «بناءً على إقرارك بحالة العقار (استرشاديّ — لم يُعايَن ميدانياً): قِيسَ الرقم على «{price-position label}» في منطقتك (عيّنة سوقيّة موثوقة، عددها {n})».
- **§١ neigh** → the attestation paragraph (stratum + indicative + inspection friction), replacing the «صفقات مثل بيتك كافية … مرجعك» claim.
- **the considered-comparables proof block** → suppressed (`&& !_isCondLead`) — the «reviewed, didn't lead» framing is stale once the stratum DID lead.
The FULL report + result screen already render `pick(v.leadership,'note')` generically → the S7 note rides that path (no new code).

## 4. Value impact (the opt-in matrix — the PO's Gate-2 artifact)

- **Blind default (no opt-in): BYTE-IDENTICAL** — Marikh 2,400,000 cost_led; all 5 villa fixtures unchanged.
- Marikh + «جيّدة/مُرمّم/جديد» + عاديّ → **3,400,000** condition_stratum_led (modern stratum, indicative, low=cost floor 2.4M).
- Marikh + «جيّدة» + راقٍ → **5,300,000** (luxury stratum).
- Marikh + «يحتاج صيانة» / «آيل للهدم» → **2,400,000** (floor, unchanged — guard).
Full table + guards: `docs/GATE2_b113_condition_axis_optin.md`.

## 5. Verification (measured)

- Isolated `test_sprint_2_22_0b113.py` **33/33** (E14, the REAL `_condition_stratum_lead` + strata shape + source wiring: blind/teardown/maintenance→None · positive→matching reliable stratum · finish→luxury · <floor→None · unreliable→None · price-position labels · the note friction AR+EN · the branched cost_led wiring + else-verbatim + ISS-A07 recompute · the refine friction note · the short-report basisLn/neigh/proof honesty overrides · stratum_label fields · version format).
- **1 R6/Lesson-2 re-point** (intent preserved): `test_sprint_2_22_0b104.py` — the keystone-proof gate literal `if(_kc&&_kc.rows&&_kc.rows.length){` → `…&&!_isCondLead){` (the proof block is otherwise unchanged; suppressed only on a condition-led card) = 19/19. Zero assertion weakened.
- DoD: aggregator **395/395 MATCH** · security **16/16** · surface-honesty **45/45** · broad walk **167/167 ALL GREEN** (166→167, +b113; **only the b104 re-point** — the S7 branch preserves the existing cost_led block verbatim, so no other sibling structural pin broke).
- py_compile OK · `node --check` OK.
- **Local E2E (live GIS, Marikh 54/541/6):** BLIND → **2,400,000 cost_led** (byte-identical) · condition=good → **3,400,000 condition_stratum_led** (modern «الشريحة المتوسّطة سعراً», n=11, low=2.4M/high=5.4M, note AR+EN present) · condition=good+luxury → **5,300,000** (luxury) · teardown → **1,800,000** (the b4 teardown lever, correctly NOT S7).
- **R14 real preview 375×812** (DOM-measured, AR + EN): the refine friction note renders (indicative + inspection friction); the condition-led short report shows the honest attestation basis + stratum label «الشريحة المتوسّطة سعراً» + friction, with **NO false «matched sales» claim** and **NO stale considered rows** (AR + EN); the full report renders the S7 leadership note (AR + EN, price-position + amount ٣٬٤٠٠٬٠٠٠); the **BLIND cost_led short report is untouched** (2.4M, «لماذا أقل» + cost basisLn intact, no S7 leak); geo/matched/e25 short reports render clean with no S7 leak; **0 console errors** throughout.
- **Personas:** lawyer APPROVE (the opt-in is disclosed as an **ordinary Assumption + a limitation on inspection** [VPS 2 / VPGA 10], NOT a Special Assumption — Gemini C1 corrected #54; «ليس تقييماً معتمداً» kept; the inspection-consequence friction raises defensibility; the number can only be lifted to a **reliable market sample**, never invented, never below the informed floor) · linguist APPROVE (register-consistent فصحى مهنية; the b100 price-position labels avoid the unmeasured-age «حديثة» claim; accurate EN twins; «استرشاديّ» not «تجريبيّ»/beta — the live-not-beta directive).

## 6. Deployment

- 🚫 **NOT deployed.** Gate-2: `docs/GATE2_b113_condition_axis_optin.md` (the opt-in matrix + guards) awaits the PO's explicit sign-off; then the ritual `git push origin master` FIRST, then `git subtree push --prefix "deploy v2" heroku master` (§20.112).

## 7. Verification curl (post-deploy, when signed)

- `/api/health` → `3.1.0-sprint2.22.0b.113`.
- the 5-fixture villa byte-gate **byte-identical to v275** (blind default unchanged).
- `POST /api/evaluate/details {zone:54,street:541,building:6,condition:"good"}` → `valuation.leadership.rule = "condition_stratum_led"`, `amount 3,400,000`, `leadership.note_ar` present.

## 8. What's NOT in this patch

- **The calibration is indicative, NOT n≥20** (the honesty residual, brief §3/§4): the (condition → stratum) mapping ships **disclosed-and-indicative** at the reliable stratum's own n; it self-tightens as **documented GT** arrives via the b71 `condition_adjustments.sqlite` («الرقم يتغيّر لا الكود», the D-3 track) — **no code change** when GT lands.
- The refine screen's condition/finish inputs are the EXISTING fields (surfaced neutrally); the raw Arabic refine labels are the pre-existing EN gap (§20.113), out of scope.
- Real villa time-adjustment (the R-3 second half) + the numeric MUC ±% range remain deferred Gate-2 items.

# Gate-2 sign-off — Sprint 2.22.0b.113 (S7 / الجوهر / B-2): the condition-axis opt-in blast radius

**Status:** 🔴 **awaiting the PO's sign-off BEFORE deploy** (same Gate-2 discipline as S4/b109). The build is complete + all-gates-green LOCALLY; **nothing is deployed.**
**What the PO is signing:** that the opt-in behavior below (the only value-affecting surface) is correct + honest to ship. The blind default is byte-identical, so **live no-attestation traffic is unaffected** — this sign-off is purely about what happens when an owner *explicitly attests* a condition.

---

## 1. The one-line summary

S7 is **opt-in only.** A cost-led villa's headline moves **only** when the owner explicitly attests a **positive** condition on the refine screen; then the number leads with the matching **reliable price-position market stratum** (indicative, disclosed) instead of the conservative cost floor. No attestation → the floor stays, **byte-identical**. A negative attestation (needs-work / teardown) never lifts.

## 2. The opt-in matrix — measured LIVE on the anchor (Marikh 54/541/6, cost-led, 17yr)

| owner's refine input | amount | rule | leads with | n | low (floor) | high | note |
|---|---|---|---|---|---|---|---|
| **(blind — no attestation)** | **2,400,000** | `cost_led` | cost floor | — | 2,400,000 | 5,400,000 | **byte-identical to v275** |
| condition = جيّدة, عاديّ | **3,400,000** | `condition_stratum_led` | modern «الشريحة المتوسّطة سعراً» | 11 | 2,400,000 | 5,400,000 | +42% opt-in lift |
| condition = مُرمّم, عاديّ | **3,400,000** | `condition_stratum_led` | modern «الشريحة المتوسّطة سعراً» | 11 | 2,600,000 | 5,400,000 | floor rises with the DRC condition |
| condition = جديد, عاديّ | **3,400,000** | `condition_stratum_led` | modern «الشريحة المتوسّطة سعراً» | 11 | 2,500,000 | 5,400,000 | — |
| condition = جيّدة, **راقٍ** | **5,300,000** | `condition_stratum_led` | luxury «الشريحة الأعلى سعراً» | 15 | 2,800,000 | 5,400,000 | luxury finish → top tier |
| condition = يحتاج صيانة | **2,400,000** | `cost_led` | cost floor | — | 2,400,000 | 5,400,000 | **guard — no lift** |
| condition = آيل للهدم | **1,800,000** | (b4 teardown) | land − demolition | — | 1,500,000 | 1,900,000 | the existing b4 lever, **DOWN** (not S7) |

**Reading the guards from the matrix:**
- The number can only be **lifted to a reliable market sample** (n≥10), never invented and **never below the cost floor** (`amount ≥ low` on every row).
- «يحتاج صيانة» / neutral / blind → the floor keeps the lead (no positive signal = no lift — the E25/R7 rail: cost is a floor, never chased up).
- «آيل للهدم» is owned by the existing b4 teardown lever (a DOWN move to land−demolition), untouched by S7.
- The `low` (the DRC cost floor) legitimately tracks condition (a renovated/new building has a higher depreciated value) — this is the existing DRC behavior, and `amount ≥ low` always holds.

## 3. The blind byte-gate (the standing invariant — unaffected)

S7 lives entirely inside the b20 `cost_led` branch, and only inside `if _s7:` (which requires a positive attestation). The `else` is the existing cost_led block **byte-for-byte**. The four non-cost-led fixtures never enter the branch at all.

| fixture | rule | blind amount | S7 reachable? |
|---|---|---|---|
| 54/541/6 Marikh | cost_led | **2,400,000** | yes — but `_s7=None` when blind → **else verbatim → byte-identical** ✓ (measured) |
| 56/647/6 V001 | geo_full | 3,800,000 | no (not cost_led) — untouched by construction |
| 55/296/13 المعراض | e25_capped | 2,600,000 | no — untouched |
| 56/565/21 أبو هامور | matched | 2,400,000 | no — untouched |
| 52/903/90 شقق | refusal | (refusal) | no — untouched |

→ **the 5-fixture villa byte-gate is byte-identical to v275 on the blind path** (measured on the cost-led anchor; guaranteed by construction on the other four).

## 4. Honesty posture (what the disclosures say)

- **On the number:** the leadership note (full report + result screen) + the short-report §١ basis line both state: «بناءً على إقرارك بحالة العقار (**استرشاديّ — لم يُعايَن ميدانياً**): قِيسَ الرقم على «{price-position label}» في منطقتك (عيّنة سوقيّة موثوقة، عددها {n})». The stale «N صفقة مطابقة، وسيطها مرجعك» / «اطّلعنا عليها ولم تقُد الرقم» framings are suppressed on a condition-led card (they would misstate the basis).
- **The friction (Gemini C2, an honest deterrent — not a dark pattern):** the refine opt-in carries «وأيّ عدم دقّةٍ في إقرارك تجعله غير صالحٍ عند الفحص الميدانيّ من البنوك أو المشترين» — a true statement that reduces over-claiming. There is **no** «🔒 unlock your higher value» framing (rejected in r9/#54).
- **RICS (Gemini C1, #54):** a user-stated condition that applies at the valuation date is disclosed as an **ordinary Assumption + a limitation on inspection** (VPS 2 / VPGA 10), **NOT a Special Assumption**. «ليس تقييماً معتمداً» kept.
- **Labels (Gemini C3, #54):** the target tier is labelled by its **b100 price position** («الشريحة المتوسّطة/الأعلى سعراً»), never by an unmeasured age word («حديثة») — a maintained 17yr villa is «مُصانة», not «حديثة».
- **Calibration (Gemini C4, #54):** the (condition → stratum) mapping ships **indicative-and-disclosed** at the reliable stratum's own n; it self-tightens as **documented GT** arrives (the b71 `condition_adjustments.sqlite`, «الرقم يتغيّر لا الكود») — **no re-code** when GT lands. Labelled «استرشاديّ», not «تجريبيّ»/beta.

## 5. What the PO signs

1. **The opt-in matrix (§2)** is correct + safe to ship (the +42% modern-stratum lift on a positive attestation; the luxury path; the maintenance/teardown guards).
2. **The indicative-not-calibrated posture (§4)** — ship at the current reliable n, disclosed; tightens with GT, no re-code.
3. Then: `git push origin master` FIRST → `git subtree push --prefix "deploy v2" heroku master` → the live 5-fixture blind byte-gate + one `condition=good` live smoke.

**Until signed, S7 stays local** (built + all-gates-green: isolated 33/33 · DoD 395/16/45 · broad 167/167 · R14 AR+EN 0 console · CHANGELOG_v193).

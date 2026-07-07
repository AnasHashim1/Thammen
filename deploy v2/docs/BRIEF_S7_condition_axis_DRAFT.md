# DRAFT BRIEF — S7 (b111) «نافذة أسئلة حالة العقار — الرقم يتكيّف مع الحالة» (الجوهر / B-2)

**Status:** 🔴 **DRAFT — awaiting PO signature BEFORE build** (Gate-2 value-affecting; the plan gates S7 on a signed brief).
**Live now:** b110 (local; not deployed). **Design source:** `docs/CONSULT_gemini_r9_median_vs_cost.md` (Path A, Rule-#54-adjudicated).
**Why held:** S7 lets a user's condition attestation move the HEADLINE (e.g. Marikh 2.4M cost-floor → 3.36M market-stratum, +40%). That is a methodology change (HARD GATE 2) + the (condition→stratum) mapping is a decision only the PO signs.

---

## 1. The problem (measured, r9)
The cost floor (DRC) structurally **under-prices a functional villa** in an appreciating land market: on Marikh (17yr, condition unknown) the engine leads with the cost floor **2.4M**, while the reliable MARKET strata it already computes say: land-priced 2.25M · **modern (1.5–2.2× land, n=11, reliable) 3.36M** · luxury (≥2.2×, n=15, reliable) 5.27M. A normal maintained 17yr villa ≈ the modern stratum **3.36M** — a reliable market number the engine owns but does not lead with (because condition is unknown, so it stays conservative).

## 2. The mechanism (Path A — Gemini-adjudicated, guards locked)
A **neutral 3-question opt-in** (the fields ALREADY exist on the refine screen — surface them neutrally):
- عمر تقريبيّ [نطاقات] · حالة عامّة (جيّدة / متوسّطة / تحتاج ترميماً) · مستوى تشطيب (عاديّ / راقٍ)
- copy: «قد يرتفع الرقم أو ينخفض — وهي إقرارٌ منك، والتقدير يبقى غير معتمد» (**NO** 🔒 unlock-dark-pattern — Gemini's 🔒 framing was REJECTED #54: it biases users to over-claim «modern» → corrupts the signal → over-valuation).

On a **confirmed condition**, the engine leads with the **matching market stratum** (indicative, n≥10, disclosed) instead of the cost floor. Otherwise (blind default, no opt-in) the conservative cost floor stays — **byte-identical** (the 5-fixture gate holds; opt-in only moves).

## 3. THE DECISION THE PO MUST SIGN — the (condition/finish/age → stratum) mapping
This is the crux. A proposed mapping (PO to sign / amend). **⚠️ Gemini C3 catch (ACCEPTED #54):** the stratum
the number leads with must be labelled to the user by its **PRICE POSITION (the b100 lexicon)**, NOT by an age
word — a 17yr well-maintained villa is «مُصانة», not «حديثة»; calling the target «الشريحة الحديثة» re-introduces
the unmeasured-age claim we already fixed in b100/r9. The internal stratum name («modern») stays internal.

| user attestation | leads with (INTERNAL stratum) | **user-facing label (b100 price-position)** | guard |
|---|---|---|---|
| تحتاج ترميماً / teardown | cost floor / land-priced | «قريبة من سعر الأرض» | never raised |
| متوسّطة + عاديّ | cost floor | «قريبة من سعر الأرض» | never raised (conservative — no lift without a positive signal) |
| **جيّدة + عاديّ** (not old) | modern (1.5–2.2× land, n≥10) | **«الشريحة المتوسّطة سعراً»** | only if reliable (n≥10) AND ≥ cost floor |
| **جيّدة/ممتازة + راقٍ** | luxury (≥2.2× land, n≥10) | **«الشريحة الأعلى سعراً»** | only if reliable AND finish = «راقٍ» |

**Open calibration question (honesty):** does «good condition, 17yr, ordinary finish» really == the modern
stratum? The r9 verdict is «indicative at n=11» — **disclosed, NOT calibrated to n≥20**. The durable
calibration (the b71 `condition_adjustments.sqlite`, currently n=1 seed from V001) tightens only with
**documented GT (n≥20)** — the PO's «الرقم يتغيّر لا الكود» decision. So S7 ships the mapping as **indicative +
disclosed**, and it self-tightens as GT arrives (no code change — «الرقم يتغيّر لا الكود»). **Gemini C4 (BOTH
runs, ACCEPTED substance):** ship it indicative-and-disclosed now (AVMs improve via the live feedback loop /
IVS 105 back-testing) — **but label it «استرشاديّ», NOT «تجريبيّ»/beta** (the standing live-not-beta directive;
CC REJECTED Gemini's «نسخة تجريبية» wording).

## 4. Guards (non-negotiable)
- **Blind default byte-identical** — the 5-fixture villa gate must hold; the opt-in is the ONLY mover.
- **Teardown/poor never raised** — a positive attestation is required to lift; «تحتاج ترميماً» keeps the floor (the E25/R7 rail: cost is a floor, never chased up on ASK).
- **b20 leadership gate + E26 age rail untouched** for the blind path.
- **Indicative + disclosed** — the stratum lead is «استرشاديّ» at n≥10; «ليس تقييماً معتمداً» kept.
- **Neutral opt-in** — «قد يرتفع أو ينخفض», never «unlock your higher value».
- **⚠️ Gemini C1 correction (ACCEPTED #54):** the user-stated condition is disclosed as an **ordinary
  Assumption + a limitation on inspection** (VPS 2 / VPGA), **NOT a «Special Assumption»** — both Gemini runs
  called it a Special Assumption, but a stated condition that *applies at the valuation date* is an ordinary
  Assumption (a Special Assumption is contrary-to-fact); our prior primary-source check (§20.27) confirms.
- **⚠️ Gemini C2 (ACCEPTED #54) — inspection-consequence friction** (an honest deterrent, not a dark pattern):
  the opt-in copy carries «أيّ عدم دقّة في إقرارك تجعل هذا التقييم غير صالح عند الفحص الميدانيّ من البنوك أو
  المشترين» — a true statement that reduces over-claiming. (Future enhancement, Gemini run-1: an optional photo
  upload — even un-analysed, asking for one reduces false «راقٍ» claims.)

## 5. Value impact (the before/after the PO signs off, like S4)
- Blind default (no opt-in): **byte-identical** (Marikh 2.4M cost-led, all 5 fixtures unchanged).
- Marikh + «جيّدة + عاديّ» opt-in → **3.36M** (the modern stratum, indicative, disclosed) — the +40% move.
- Marikh + «تحتاج ترميماً» → **2.4M** (floor, unchanged — guard).
- A live blast-radius on the opt-in paths (like S4) will accompany the build for the PO's review.

## 6. What I need from the PO to build S7
1. **Sign / amend the §3 mapping** (which attestation leads which stratum, and the reliability threshold n≥10).
2. **Confirm the §4 guards** (esp. teardown-never-raised + blind-default-byte-identical).
3. **Confirm the indicative-not-calibrated posture** (ship at current n, disclosed; tightens with GT — no re-code).
4. Then: recon the exact (condition→stratum) code path (the b20 gate interaction) → build → the opt-in blast-radius table → **your sign-off on that table before deploy** (same Gate-2 discipline as S4).

**Until §1–§3 are signed, S7 is not built.** Everything else in the queue (R1–R3, S1–S5) is built + local; S4 additionally awaits your sign-off on its before/after table (`docs/GATE2_b109_land_geo_filter_blast_radius.md`).

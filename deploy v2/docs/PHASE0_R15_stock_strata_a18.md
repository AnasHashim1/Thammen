# PHASE 0 — R15 §5 audit: stock_strata land-median a18-awareness — READ-ONLY

> **Status:** Phase-0 audit (NO edit, NO deploy). Production byte-identical (Heroku **v161** / a22).
> Characterise before fixing; fix + Gate decision deferred to results (below).
> **Brief:** `docs/BRIEF_R15_stock_strata_a18_audit.md`. **Authored:** CC, 2026-06-04.
> **Method:** live `/api/evaluate` (4 anchors, browser-UA #61) for the per-prop deltas + offline
> production helpers (`moj_reference.area_match_key`, `categorize`; `stock_strata.compute_land_median`)
> on `moj_weekly.csv` for scope + code trace of the consumer chain (E14).

---

## TL;DR
| | Verdict |
|---|---|
| **Hypothesis** | ✅ **CONFIRMED.** `stock_strata.compute_land_median` matches areas with `_norm` (exact) — NOT a18 `area_match_key` — so it drops zone-number siblings + override-aliases → a **narrower, higher** land pool. |
| **Magnitude** | **+2.4% to +7.0%** on the 4 live anchors (stock_strata land median runs **HIGH**); offline scope |delta| median **3.0%**, max ~40% in thin areas. |
| **Direction** | **stock_strata OVER-states** the land median (drops the lower-priced siblings) → **under-states the E4 ratio** → strata cards skew toward `land_priced`/`aging` (under-credit the building). |
| **Blast radius** | **Display only.** Strata cards (user-visible) + income-crosscheck `stock_class` + a **conditional** listing-gap warning. **NOT the headline `valuation.amount`. NOT the B-1 `value_floor`** (that's a18-aware via `moj_reference`). |
| **Go / no-go** | 🟢 **GO** — worth fixing: post-B-1 the strata card shows a land-reference median **~+2-7% higher than the value_floor's land number in the SAME response** (a visible internal inconsistency). |
| **Gate** | **Gate-2 (user-facing display), headline VALUE-INVARIANT.** The fix changes the strata cards + the conditional warning %, NOT the headline or the floor → re-smoke proves zero headline drift; strata-card change needs an Anas sign-off. **NOT** value-invariant on the strata-card surface. |

---

## Step 1+2 — per-property divergence (LIVE measured, v161)
`vd_land` = `value_decomposition.land` (a18-aware `moj_reference`, the B-1 floor basis) · `strata_land` =
`stock_strata.land_reference` (`_norm` exact). All four areas have sibling/alias variants.

| area / PIN | vd_land (a18) | strata_land (current) | Δ | sign | n drop |
|---|---|---|---|---|---|
| المعمورة 56/647/6 | 3,768 (n=20) | 4,032 (n=13) | **+7.0%** | strata HIGH | −7 |
| بو هامور 56/565/21 | 3,778 (n=33) | 3,875 (n=20) | **+2.6%** | strata HIGH | −13 |
| امريخ 54/541/6 (→مريخ override) | 3,020 (n=34) | 3,212 (n=18) | **+6.4%** | strata HIGH | −16 |
| المعراض 55/296/13 | 2,547 (n=25)* | 2,607 (n=11) | **+2.4%** | strata HIGH | −14 |

*المعراض vd via the B-1 **F1 recompute** (Patch-C suppressed `value_decomposition`). All four: stock_strata
sees **fewer** comps and a **higher** median → it drops the lower-priced a18 siblings.

## Step 3 — consumer map (blast radius), traced in `evaluate_unified.py`
`stock_strata` is built at `:3830` from `geo_v2.primary.moj_names` + `compute_land_median`
(`stock_strata.py:208`, `_norm` exact). Its land-median feeds, in order:
1. **Strata cards** → `output['stock_strata']` (`:4529`) → rendered `index.html:1175-1250`
   (`land_reference.median_per_m2` @1190 + per-stratum medians + `dominant_stratum`). **USER-VISIBLE** (desktop + mobile).
2. **`dominant_stock_class`** → `_build_income_crosscheck(stock_class=…)` (`:3875`). Income = cross-check (villa headline is comparison) → **display, not headline**.
3. **Subject classification → market-position benchmark swap** (`:3253-3263`, Sprint 2.16.2): IF the subject
   classifies into a **reliable (n≥10)** stratum, the listing-vs-benchmark gap uses that stratum's
   `estimated_total` → feeds **`sanity_warnings`** (`:3265-3276`) ONLY. **Fires only when a `listing_price`
   is supplied.** Does **NOT** write `valuation.amount`.
4. **NOT `valuation.amount`** — exposure-only by design (`:3812` "Headline value unchanged"); the swapped
   `benchmark` feeds warnings, never the headline.
5. **NOT `value_floor.land_floor`** (B-1) — that reads `value_decomposition.land` / recomputes from
   `moj_reference` (a18-aware). **Independent of stock_strata** (Phase-0 Sprint-B Q5).

⟹ **The headline + the B-1 land floor are SAFE.** R15 is a **display/transparency** divergence.

## Step 4 — index.html render
`stock_strata` IS user-visible: the strata cards (`index.html:1178` `if(stockStrata && .applied && .strata)`)
render `land_reference` (@1190), each stratum's median, and the `dominant_stratum` label + share + note
(@1247-1250). So the divergent land-reference median **is shown to the user** — and now sits next to the
B-1 `value_floor` land number (a18) in the same report → the inconsistency is visible. (Backend-derived;
render is an unconstrained block — no overflow concern.)

## Step 5 — scope (offline, all MoJ land rows)
- 14,155 land rows → **125 a18 land keys; 14 have zone-number siblings** (>1 `_norm` sub-name) → **~11%** of
  land areas hit by the zone-number case. **PLUS** the `GIS_TO_MOJ_NAME_OVERRIDES` alias cases (امريخ
  الجنوبي→مريخ, جزيرة اللؤلؤة→اللؤلؤة, السلطة الجديدة, لجميليه — ~5 more) that `compute_land_median` also
  ignores (it has neither `area_match_key` nor the overrides) — **NOT** in the 14, so true scope ≈ **~15-19 areas**.
- Sibling-area land-median delta (a18 pool vs largest single sub-name): **|delta| median 3.0%, max 39.9%,
  3/12 >5%, 9/12 >2%; signed median +2.5%** (narrow pool over-states). Large outliers (فريج بن محمود +21%,
  الغانم العتيق +40%) are **thin** (a18 n=24/11) → high variance, low traffic.
- Most-trafficked sibling areas: الثمامة (n1004) −1.5%, ازغوى (n421) +2.7%, معيذر (n412) −2.1%, نعيجة (n327)
  +2.4%, المعمورة (n92) +4.3% — so the **common** case is a modest few-percent skew; the live villa anchors
  (bracket-aware path) land at +2.4–7.0%.

## Root cause
`stock_strata.compute_land_median` (`stock_strata.py:249`) resolves areas with
`names_normalized = {_norm(n) for n in moj_area_names}` then exact-membership — it never applies
`moj_reference.area_match_key` (zone-number strip + hamza-fold) **nor** the `GIS_TO_MOJ_NAME_OVERRIDES`. So
it sees only the names `geo_v2` passed, missing sibling/alias land rows the a18 `build_reference` (and thus
the B-1 floor) pools. a18 (Sprint 2.22.0a.18) wired `area_match_key` into `moj_reference` + `compute_trend`
but **not** into `stock_strata` — the same family as the still-open a12 "`compute_trend` categorizer
alignment" debt.

## Go / no-go + proposed surgical fix
- **GO.** The headline + floor are safe, but post-B-1 the strata card's land reference visibly disagrees
  (~+2-7%) with the value_floor's land number in the same report — an internal-consistency defect now that
  both are surfaced. Fixing also makes the E4 classification more accurate (the +2-7% over-statement
  currently under-credits the building → mild `land_priced`/`aging` skew).
- **Surgical fix (one function):** route `compute_land_median`'s area matching through
  `moj_reference.area_match_key` (+ apply `GIS_TO_MOJ_NAME_OVERRIDES`) instead of `_norm` exact — i.e. pool
  the a18 siblings/aliases, exactly as `build_reference` does. ~3-8 lines + an import. (Alternatively: pass
  geo_v2's resolved name through `area_match_key` before handing it to stock_strata.)
- **Gate:** **Gate-2 (user-facing display change), headline VALUE-INVARIANT.** It changes the strata cards
  (land reference + classification) and, only when a `listing_price` is supplied, the listing-gap warning %
  — it does **not** change `valuation.amount` or `value_floor`. So: re-smoke the 4 anchors to prove
  **headline + value_floor byte-identical**, and treat the strata-card change as the signed deliverable.
  **Not** value-invariant on the strata-card surface → needs an Anas sign-off (a small Gate-2 brief).

## 🔮 Forward-risk + the decision this feeds
- 🔮 The fix shifts the **E4 stratum classification** (land median drops ~2-7% → ratios rise → some boundary
  comps move toward `aging`/`modern`; a `dominant_stratum` could flip for a few properties → the strata-card
  narrative changes). Guard: the fix DoD must re-smoke the 4 anchors for **zero** headline/value_floor drift
  + spot-check that the strata-card `land_reference` now equals the `value_floor` land number (the
  consistency win), and that no `dominant_stratum` flip is spurious.
- 🔮 The **conditional listing-gap warning** % shifts when a `listing_price` is supplied + a reliable stratum
  is hit — include a listing-price case in the fix smoke.
- **القرار المطلوب (Anas):** **go/no-go on the fix.** If GO → it's a **small Gate-2 sprint** (sign-off on the
  strata-card change; headline value-invariant): route `compute_land_median` through `area_match_key` +
  overrides, isolated test (strata land == moj_reference land on the anchors; classification re-derived),
  DoD, Gate-1 deploy + re-smoke (56/565/21, 54/541/6, 55/296/13, 56/647/6 — headline + value_floor
  byte-identical). CC recommends **GO** (it closes the now-visible internal inconsistency + improves E4
  accuracy; risk is bounded to display).

## Out of scope
The headline value, the B-1 `value_floor` (a18-aware already), and any non-villa path. `compute_trend`
categorizer alignment (a12 debt — same family, separate). The override-alias completeness (فريج العسيري etc.,
a18-deferred) is unchanged.

---
*Phase-0 R15 audit — READ-ONLY, production byte-identical (v161). Hand back: Anas's go/no-go → (if GO) a
small Gate-2 fix brief → build + Gate-1 deploy.*

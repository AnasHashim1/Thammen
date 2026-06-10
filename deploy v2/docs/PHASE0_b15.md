# PHASE-0 — Sprint 2.22.0b.15 (screen 4: polished result) — panel inventory + tier map

> Read-only recon per `BRIEF_Sprint2p22p0b15_screens45_SIGNED.md` §4. Measured on the live `index.html`
> (b14 tree, 2129 lines; `show()` = lines 983–1649). **VERDICT: NO HALT — no tier demotion hides a
> compliance surface** (the compliance set below stays always-visible by design). Date: 2026-06-10.

## §1 — Panel inventory (show(), current render order) → tier assignment

| # | Panel (lines) | Condition | b15 tier |
|---|---|---|---|
| 0 | Copy / Print buttons (1010-1012) | always | keep (utility, top) |
| 1 | **MUC clause card** (1014-1048) | `muc_ar` | **ALWAYS-VISIBLE (compliance)** — moves to directly AFTER the TIER-1 block; a MUC **chip** joins TIER-1 |
| 2 | RICS/IVS note `<details>` (1050-1060, a8) | note present | already collapsed-by-default — keep as-is (de-facto TIER-2) |
| 3 | A11 subtype/zoning mismatch (1062-1082) | `szm` | alert — stays visible, ABOVE TIER-1 (qualifies the result) |
| 4 | Asset-type reality check (1084-1099) | `atr` | alert — stays visible, ABOVE TIER-1 |
| 5 | Multi-QARS flag + override input (1101-1133) | `mqr.detected` | alert + ACTION (override input) — stays visible, ABOVE TIER-1 |
| 6 | Service-scope badge (1135-1150) | `ss` | status surface (incl. requires/disclaimer text) — stays visible, ABOVE TIER-1 |
| 7 | Sanity warnings (1152-1158) | `sw.length` | alert — verbatim «قبل قراءة النتيجة» → MUST precede the number; stays ABOVE TIER-1 |
| 8 | Insufficient-data card (1160-1194) | `!hasValuation` | **refusal path UNCHANGED** — tiering applies to the valued path only (hiding refusal explanations behind accordions would be a regression) |
| 9 | Main info card: address/district/area/type/zoning/height + b9 `pbRows` + map (1196-1218) | `hasValuation` | **TIER-2 accordion «بيانات العقار الأساسية»** (brief lists property-basis as TIER-2) |
| 10 | Methodology bare line (1220-1223, a4) | `methodology_ar` | kept VISIBLE (1 line; the a4 honesty surface) — under TIER-1 |
| 11 | Valuation card: tier badge + range headline (b3) + median + condition note (a17/a19) + teardown/luxury (b4) + value_floor (B-1) + hbu (b12) + n row (1225-1273) | `hasValuation` | **TIER-1 core** — augmented with: MUC chip + «ليس تقييماً معتمداً» line + evidence one-row summary. The honesty notes (condition / value_floor / hbu / teardown / luxury) and the n row (cite-n discipline) STAY attached to the headline |
| 12 | Evidence-quality panel, full (1274, b2.2) | `hasValuation` | one-row summary → TIER-1 · full panel → **TIER-2 accordion «جودة الأدلّة (تفصيل)»** |
| 13 | Brief sections loop (1277-1282) | `br.sections` | valued path: **each section = its own TIER-2 accordion** (incl. the cap-rate panel `cap_rate_provenance`) · refusal path: flat as today |
| 14 | Value decomposition, b14 narrative (1284-1330) | `v.value_decomposition` | **TIER-2 accordion «تفكيك القيمة (أرض + بناء)»** |
| 15 | Building substantiality / 10-Year (1332-1380) | `v.building_substantiality` | **TIER-2 accordion «عمر البناء وقاعدة الـ10 سنوات»** |
| 16 | Geometry card + refine button (1382-1419) | geometry + building | info → **TIER-2 accordion «الهندسة ومساحة البناء»** · the refine CTA itself → **TIER-3** |
| 17 | Building-details-missing notice (1421-1431) | no user details | TIER-3 region (it motivates the refine CTA) |
| 18 | Range-expansion explanation (1433-1450) | `v.range_expansion` | TIER-2 accordion |
| 19 | Trend card (1452-1478) | `trend.years` | TIER-2 accordion |
| 20 | Geometric findings (1480-1519) | `geometric_factors` | TIER-2 accordion |
| 21 | Location features (1521-1529) | `location_features` | TIER-2 accordion |
| 22 | Stock strata (1531-1616) | `stock_strata.applied` | **TIER-2 accordion «تصنيف المخزون»** (brief-listed) |
| 23 | Known unknowns (1618-1624) | `reasoning_trace` | TIER-2 accordion «ما لا نعرفه (يحتاج فحص ميداني)» |
| 24 | Data-freshness caveat (1626-1630) | caveat present | **ALWAYS-VISIBLE** (staleness transparency, Sprint 2.7 commitment; MoJ 161d stale today) |
| 25 | Disclaimer card (1632-1635) | `d.disclaimer` | **ALWAYS-VISIBLE (compliance)** |
| 26 | verification_url footer (1637-1646) | url present | visible (tiny) |
| 27 | Static `.disc` footer (markup 502-513): «إرشادي… لا يُعتبر تثميناً رسمياً» + Terms (a24) + CC BY 4.0 attribution (a25) | always | **UNTOUCHED** (outside `rOut`) |

## §2 — Compliance always-visible set (the §4 HALT check)

MUC clause card · the NEW TIER-1 «ليس تقييماً معتمداً» line (verbatim a20 `rics_compliant_status_ar` as suffix
when present) · data-freshness caveat · `d.disclaimer` card · static footer (إرشادي + Terms + attribution) ·
all alert cards (A11 / reality / sanity / multi-QARS incl. its override action) · service-scope badge ·
methodology bare line (a4) · the moj n row (cite-n) · the headline honesty notes (a17/a19 condition, B-1
value_floor, b12 hbu, b4 teardown/luxury). **None of these is collapsed → NO HALT.**

## §3 — Findings that shape the build

- **F1 (print-parity regression risk).** Closed `<details>` do not print their content; today's print view
  prints the full stack. → `printReport()` + `beforeprint`/`afterprint` handlers force-open all `#rOut details`
  for printing and restore state after. In-scope (prevents b15 degrading the print path b17 will replace).
- **F2 (report CTA target).** Screen 5 ships in b17 → in b15 the TIER-3 «التقرير الكامل» CTA triggers the
  existing `printReport()` (today's report surface); b17 rewires it to the report screen. No info loss.
- **F3 (refusal path).** All tier-2 wrapping is gated on `hasValuation`; refusal layout byte-equivalent flat.
- **F4 (MUC chip source).** `material_uncertainty.level` ∈ {low, medium/moderate, high, critical} → chip
  «تحفظ مادي: منخفض/متوسط/مرتفع/حرج»; chip renders only when the MUC clause itself is present.
- **F5 (evidence one-row).** Reuses `_evidenceRatings(d)` verbatim (derive-don't-author §2c) — 4 compact
  pills; the FULL b2.2 panel (incl. the explanation footer) moves intact into its accordion.
- **F6 (a8 note).** Already a collapsed `<details>` — counts as tier-2 today; position kept.
- **F7 (mechanism).** Native `<details>/<summary>` accordions (the proven a8 pattern): zero new JS libraries,
  keyboard/touch accessible by default; one shared `.t2acc` CSS class on theme variables.
- **F8 (MUC card position).** The full clause card moves from FIRST to directly after TIER-1 (v4: the range
  arrives first) — it remains always-visible + prominent; the TIER-1 chip guarantees first-glance visibility.
- **F9 (mockup status).** `thammen_owner_flow_mockup.html` consulted as reference only (NOT a spec, per brief).

## §4 — Value-invariance contract

Frontend-only (`index.html`) + the 2 ENGINE_VERSION/SPRINT_TAG lines in `evaluate_unified.py`; `api.py`
UNTOUCHED. The numeric contract (amounts/ranges/methods/floors) on the 4 anchors + V001 is byte-identical
by construction; text/layout diffs are BY DESIGN (brief header).

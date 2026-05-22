# Sprint 2.21.0.5 — Land Output Polish — DRAFT for review

**Status:** DRAFT for review. **No code until approved** (§5).
**Baseline:** Sprint 2.21.0 (`thammen-sprint2p21p0-pin-input-lands`, deployed)
**Target:** `thammen-sprint2p21p0p5-land-output-polish` · CHANGELOG_v41
**Type:** Output-template polish — conditional rendering for `raw_land`. **Backend
already correct** (PIN→raw_land→grid verified on الخور: 1.2M, n=79 reliable). This
only fixes the *user-facing template* which still assumes a building exists.
**Effort:** 2-4h.

---

## 0. Root cause (Rule #46 expansion)
Pre-Sprint audit caught the *classifier* gap (correct). But the **template layer**
was not audited for the new asset_type: «backend produces raw_land» ≠ «output
template handles raw_land». Another vindication of post-deploy E2E visual testing.
**Rule #46 to expand:** the new-input-path audit must also cover **template/output
rendering** for the new mode, not just classifier output.

**Recurring theme:** `'land'` vs `'raw_land'` naming. The classifier emits
`raw_land`; some maps key on it (`ASSET_TYPE_TO_MOJ_CATEGORY` ✓ — that's why the
valuation worked), others key on `'land'` (scope_of_service ✗ — Issue 1). Fix per
module via an alias; a future cleanup could unify the literal.

---

## 1. The 5 issues — source map + fix (audited)

| # | Sev | Symptom | Source (file:line) | Fix |
|---|---|---|---|---|
| 1 | HIGH | "❌ خارج النطاق — نوع غير معروف" beside "أرض فضاء / 🟢 موثوق" | `scope_of_service.py` `_ASSET_SCOPE` has **`'land'`** (supported) but **not `'raw_land'`** → fallback unsupported ([:268](scope_of_service.py)) | Add `'raw_land'` → alias of the `'land'` scope (supported), OR normalize `raw_land→land` in `classify_asset_scope`. |
| 2 | HIGH | `address: "None/None/None"` + `valuation_id: ...-NoneNoneNone` | `evaluate_property.py` success-path builds `f'{zone}/{street}/{building}'` ([:1388](evaluate_property.py), [:1679](evaluate_property.py)); valuation_id likewise | When `pin`: address = `f'أرض في {district} — PIN {pin}'` (fallback `f'PIN {pin}'`); valuation_id uses pin. |
| 3 | HIGH | `value_decomposition`: "بناء −3.5% (−41,948)" for bare land | `evaluate_unified.py` Sprint 2.6 block runs for any plot ([:3017](evaluate_unified.py)) | If `asset_type ∈ {raw_land, land}` → **skip** decomposition; emit note «أرض فضاء — التقييم على قيمة الأرض فقط». |
| 4 | MED | factor "التقييم يفترض بناءً نموذجياً" / BUA + service-charge factors | `material_uncertainty.assess_uncertainty` factors ([:215](material_uncertainty.py), [:220](material_uncertainty.py)) | Thread `asset_type` (or `is_land`) to `assess_uncertainty`; skip building/BUA/service-charge factors for land. |
| 5 | MED | tenant/tower/building items in due-diligence + known_unknowns | due-diligence list `output_briefs.py` ([:289-293](output_briefs.py)); known_unknowns `material_uncertainty.py` ([:201-214](material_uncertainty.py)) | raw_land branch: land-specific questions (zoning R1/R2/R3, MoJ deed, site services, permitted height, legal restrictions); skip building unknowns. |

**Modules touched:** scope_of_service.py · evaluate_property.py · evaluate_unified.py · material_uncertainty.py · output_briefs.py. All changes **conditional on asset_type** → buildings/villas/etc. unchanged (additive, regression-safe).

---

## 2. raw_land due-diligence list (Issue 5, replaces building/tenant questions)
- تحقّق من تصنيف المنطقة (R1/R2/R3) — يحدّد ما يمكنك بناؤه
- اطلب بيان عقاري من وزارة العدل (يكشف الرهونات والخلافات)
- تحقّق من خدمات الموقع (كهرباء/ماء/صرف/طرق)
- اطلب ارتفاع البناء المسموح (General_Landuse)
- اسأل عن أي قيود قانونية/تخطيطية على القطعة

---

## 3. Files / version / changelog
| File | Change |
|---|---|
| `scope_of_service.py` | raw_land → supported (alias of land) |
| `evaluate_property.py` | pin-aware address + valuation_id |
| `evaluate_unified.py` | skip value_decomposition for land; land note; thread asset_type to MUC |
| `material_uncertainty.py` | asset-aware factors + known_unknowns |
| `output_briefs.py` | raw_land due-diligence branch |
| `tests/test_sprint_2p21p0p5_land_polish.py` | new |
| `CHANGELOG_v41.md` | new |
ENGINE_VERSION → `thammen-sprint2p21p0p5-land-output-polish`.

---

## 4. Pre-build audit (done — this doc) + test plan
- **Audit complete:** the 5 sources mapped above (no further code-reading needed).
- **Tests (≥5):** scope(raw_land)=supported; pin-address not "None/None/None";
  raw_land → no value_decomposition (+ note present); MUC factors exclude
  building/BUA for land; due-diligence has no tenant/building items for raw_land.
  Two-layer: one test exercises the real `evaluate_property`/`assess_uncertainty`.
- **Post-deploy:** re-run the 5 PINs (API) — confirm: scope=supported, no
  "None/None/None", no negative building value, no building-assumption factor, no
  tenant questions. Browser visual on الخور 74328443.

## 5. Pre-deploy checklist (§5)
py_compile · `node --check` N/A (no JS; index.html unchanged) · full suite green
(17→18 files) · ≥5 new tests · smoke 5 land PINs from Heroku.

## 6. Open items for sign-off
- Confirm Issue-1 fix approach (alias vs normalize) — recommend **alias**
  (`_ASSET_SCOPE['raw_land'] = _ASSET_SCOPE['land']`, lowest risk).
- Confirm the raw_land due-diligence list (§2) wording.
- After approval: code → local tests → deploy permission → re-run 5 PINs.

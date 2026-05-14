# CHANGELOG — Sprint 2.14.0: RICS Scope & Material Uncertainty Clause

**Engine version:** `thammen-sprint2p14p0-scope-and-muc`
**SPRINT_TAG:** `2.14.0` → /api/health reports `3.1.0-sprint2.14.0`
**Date:** 2026-05-14
**Files added:** `scope_of_service.py`, `market_regime.py`, `test_scope_of_service.py`, `test_material_uncertainty.py`, `test_market_regime.py`
**Files updated:** `evaluate_unified.py`, `output_briefs.py`, `material_uncertainty.py`, `api.py`, `index.html`
**Builds on:** Sprint 2.11 (context preservation), Sprint 2.7 (data freshness)

---

## Why this matters

When the user asked "هل ما نبنيه ضمن إرشادات RICS؟" the honest answer
was: partially, with significant gaps. Specifically:

1. **No formal scope statement.** RICS VPS 2 requires every valuation to
   declare what's being valued, what's excluded, and at what service
   level. Thammen previously had a generic disclaimer in /api/about but
   nothing per-response, nothing per-asset-type.

2. **No Material Uncertainty Clause.** RICS VPS 5 requires a formal MUC
   declaration during market disruption (war, crisis, structural shock).
   The recognised wording — "less certainty, and a consequently higher
   degree of caution, should be attached" — was missing from Thammen
   despite a documented market disruption since 2026-02-28.

3. **Implicit scope claims.** The UI accepted any address without
   warning the user that some asset types have no defensible methodology
   in Thammen. A user evaluating a palace got an `insufficient_data`
   error without understanding WHY palaces are different from villas.

Sprint 2.14.0 fixes all three at the foundation level, **before**
shipping the regime-adjusted recommendations of Sprint 2.14.1.

This Sprint is **defensive** by design. It restricts what Thammen claims
to do, makes uncertainty explicit, and refuses to silently overreach.
It's the honesty layer that should precede any feature.

## What this drop delivers

### NEW: `scope_of_service.py` (~280 lines)

Formal RICS VPS 2 Scope of Service for Thammen.

Three-tier classification of 10 asset types:

**Supported** (full Sales Comparison from MoJ): standalone villa, land,
small compound (≤15K m²).

**Limited** (Income/DCF, requires user input): large compound (≥50K m²),
tower, apartment building, palace.

**Unsupported** (explicitly out of scope): commercial, industrial,
agricultural.

Each entry carries: tier label, methodology used (Sales Comparison /
Income / Cost), what user input is required (if limited), and a
user-facing disclaimer explaining the classification.

The service level is declared explicitly: Thammen produces "Calculation
of Value" + "Other Advice" per RICS PS 1 / VPS 1, **not** a "Valuation
Report" — and therefore is not suitable for mortgage, court, or
financial reporting purposes. Users who need that go to a certified
RICS valuer.

### NEW: `market_regime.py` (~290 lines)

Encodes the current Qatar market regime (`post_disruption_recession`)
with 4 shock layers (post-WC correction, war/Hormuz, population
outflow, volume collapse), each with date, type, evidence source.

In Sprint 2.14.0 this module is used **only** for MUC text generation
(not yet for value adjustments — that's Sprint 2.14.1).

Calibration constants (multipliers for buyer ceiling, opening offer)
are present but unused in this Sprint. They will be activated by
Sprint 2.14.1 once we have broker-confirmed sales to validate against.

### MODIFIED: `material_uncertainty.py` (+90 lines)

Added the `regime_muc()` function that generates RICS VPS 5 MUC text
from the active market regime. Output includes:

- `muc_clause_ar` / `_en` — the formal declaration text in both languages
- `muc_basis_ar` — explanation of why MUC applies (MoJ lag, etc.)
- `muc_review_recommendation_ar` — under what conditions to re-evaluate

The MUC is automatically attached to **every** `assess_uncertainty()`
result during a non-normal regime — even when per-property uncertainty
is "low". Market-wide MUC and per-property uncertainty are independent
layers; both can fire simultaneously.

The MUC wording follows the RICS-recognised VPS 5 structure used by
Cushman & Wakefield, Knight Frank, JLL during COVID-19 and other
regional crises:
1. Identifies the cause (the regime + shock layers)
2. States "less certainty — and a consequently higher degree of caution"
3. Recommends frequent review

### MODIFIED: `evaluate_unified.py` (+45 lines)

1. **Engine version bumped:** `ENGINE_VERSION` →
   `thammen-sprint2p14p0-scope-and-muc`, `SPRINT_TAG = '2.14.0'`.

2. **NEW helper `_attach_scope()`:** classifies asset type and adds
   `service_scope` field to every response. Wrapped in try/except —
   never breaks the response.

3. **All 5 response builders wired** to call `_attach_scope()`:
   `_build_fast_insufficient_data_response`,
   `_build_fast_listing_only_response`,
   `_build_fast_income_only_response`,
   `_build_out_of_scope_response`,
   `_build_unified_output` (main pipeline).

### MODIFIED: `output_briefs.py` (+5 lines)

The `material_uncertainty` brief section now passes through the new
MUC fields (`muc_clause_ar`, `muc_clause_en`, `muc_basis_ar`,
`muc_review_recommendation_ar`) so the frontend can render the formal
RICS VPS 5 declaration prominently.

### MODIFIED: `api.py` (+17 lines)

NEW endpoint `GET /api/scope` — returns the formal scope summary for
the homepage scope modal. Backed by `service_scope_summary()`.

### MODIFIED: `index.html` (+~80 lines)

1. **Homepage:** "ما يدعمه ثمّن وما لا يدعمه ↓" link below the start
   button. Opens a modal with the 3-tier scope breakdown
   (supported / limited / unsupported) and the formal service-level
   declaration.

2. **Results page top:** RICS VPS 5 MUC banner (red, prominent) appears
   FIRST when MUC is active. Includes the clause text, basis (MoJ lag
   explanation), and review recommendation.

3. **Results page (after MUC):** Service Scope tier badge showing what
   tier this asset is in (supported/limited/unsupported), the
   methodology being applied, required user inputs (if limited), and
   the scope disclaimer.

Both use existing theme variables (`--bad`, `--bad-bg`, `--ok`, `--ok-bg`,
`--warn`, `--warn-bg`, `--alt`, `--muted`, `--primary`). No new CSS rules.

### NEW TESTS: 3 test files, 76 tests total

- `test_scope_of_service.py` — 27 tests
- `test_material_uncertainty.py` — 13 tests
- `test_market_regime.py` — 36 tests (carried from earlier Sprint 2.14 work)

All passing in 0.01s combined. Covers asset classification, MUC text
generation, regime normal/active behaviour, serialization, and the
RICS VPS 5 structural requirements (cause identified, lower certainty
stated, frequent review recommended).

---

## What this Sprint does NOT do

1. **No regime-adjusted recommendations yet.** `market_regime.py`
   contains the calibration multipliers (-10pp ceiling, -5pp old
   property) but they are **not applied** to buyer recommendations.
   That's Sprint 2.14.1, which ships after we have broker-confirmed
   sales to validate the numbers against.

2. **No engine valuation change.** `valuation.amount` is unchanged.
   Only scope metadata and MUC text are added. Existing fields stay
   the same.

3. **No buyer-brief negotiation changes.** The hardcoded MoJ × 1.10 /
   × 0.90 logic stays for now. Sprint 2.14.1 replaces it.

4. **No data freshness banner regime-rewrite.** Sprint 2.7 banner says
   "data is N days stale". Could be enhanced to say "predates regime
   by N days" — deferred to a future Sprint.

5. **No L3/L4/L5 (listings time series, building age, villa rentals).**
   These are separate work streams.

The Sprint scope was deliberately narrow: **establish honest scope
boundaries and formal RICS uncertainty disclosure before any feature
expansion**. Future Sprints build on this foundation.

---

## Verification — empirical evidence

```
$ python test_scope_of_service.py
Ran 27 tests in 0.008s — OK

$ python test_material_uncertainty.py
Ran 13 tests in 0.001s — OK

$ python test_market_regime.py
Ran 36 tests in 0.001s — OK

$ python scope_of_service.py
ثمّن يدعم 3 فئات بالكامل، 4 فئات بمنهج الدخل، و 3 فئات خارج النطاق.
✅ فلة مستقلة — تغطية MoJ كافية في 10+ مناطق سكنية رئيسية
✅ أرض سكنية — تغطية MoJ كافية...
[etc.]
```

MUC generation for an active regime:
```
⚠️ تحفظ مادي وفق RICS VPS 5
تواجه السوق العقاري القطري في تاريخ هذا التقدير (2026-02-28 وما بعده)
اضطراباً جوهرياً نشطاً: تصحيح ما بعد المونديال، الحرب الإقليمية وإغلاق
مضيق هرمز...

بناءً عليه — ووفق المعيار المعترف به في RICS VPS 5 — يجب اعتبار درجة
اليقين في هذا التقدير أقل من المعتاد، وتطبيق درجة حذر أعلى عند الاعتماد
عليه. يُوصى بمراجعة هذا التقدير على فترات متقاربة.

الأساس: بيانات وزارة العدل المسجَّلة تنتهي عند 2025-12-31 — أي قبل بدء
الاضطراب الحالي بـ 59 يوماً.
```

---

## Deployment

```cmd
cd /d "C:\Thammen\deploy v2"
```

Back up files we're modifying:

```cmd
copy /Y evaluate_unified.py evaluate_unified.py.bak1
```

```cmd
copy /Y output_briefs.py output_briefs.py.bak1
```

```cmd
copy /Y material_uncertainty.py material_uncertainty.py.bak1
```

```cmd
copy /Y api.py api.py.bak5
```

```cmd
copy /Y index.html index.html.bak1
```

Drop the new files:

```cmd
tar -xf "%USERPROFILE%\Downloads\sprint2p14p0-delta.zip"
```

Local verification (4 steps — STOP if any fails):

```cmd
python test_scope_of_service.py
```

```cmd
python test_material_uncertainty.py
```

```cmd
python test_market_regime.py
```

```cmd
python -c "import evaluate_unified; print(evaluate_unified.ENGINE_VERSION)"
```

Expected: `thammen-sprint2p14p0-scope-and-muc`.

Commit + deploy:

```cmd
git add scope_of_service.py market_regime.py test_scope_of_service.py test_material_uncertainty.py test_market_regime.py
```

```cmd
git add evaluate_unified.py output_briefs.py material_uncertainty.py api.py index.html CHANGELOG_v19.md
```

```cmd
git commit -m "Sprint 2.14.0: RICS scope + Material Uncertainty Clause"
```

```cmd
git push heroku master
```

## Verification curl (post-deploy)

```cmd
curl -s "https://thammen.qa/api/health"
```
Look for `"version":"3.1.0-sprint2.14.0"`.

```cmd
curl -s "https://thammen.qa/api/scope"
```
Should return a JSON with `supported` (3), `limited` (4), `unsupported`
(3), and the `service_level_ar` text.

```cmd
curl -s -X POST "https://thammen.qa/api/evaluate/details" -H "Content-Type: application/json" -d "{\"zone\":52,\"street\":903,\"building\":90,\"audience\":\"buyer\"}"
```

Expected new keys:
- `service_scope.tier = "supported"` (for a standalone villa)
- `service_scope.methodology_ar`
- `service_scope.disclaimer_ar`
- Inside `brief.sections` find `material_uncertainty` with new keys:
  `muc_clause_ar`, `muc_basis_ar`, `muc_review_recommendation_ar`

Then open `https://thammen.qa/?zone=52&street=903&building=90` in a
browser:
- **Homepage:** "ما يدعمه ثمّن وما لا يدعمه" link should open a modal
- **Result page:** RICS VPS 5 MUC banner at the very top (red)
- Just below: Service Scope tier badge (green for villa = supported)

Per Section 5: "present in JSON" ≠ "visible to user". Confirm both.

## Rollback

```cmd
copy /Y evaluate_unified.py.bak1 evaluate_unified.py
copy /Y output_briefs.py.bak1 output_briefs.py
copy /Y material_uncertainty.py.bak1 material_uncertainty.py
copy /Y api.py.bak5 api.py
copy /Y index.html.bak1 index.html
del scope_of_service.py market_regime.py test_scope_of_service.py test_material_uncertainty.py test_market_regime.py
git checkout -- evaluate_unified.py output_briefs.py material_uncertainty.py api.py index.html
git commit -am "Rollback Sprint 2.14.0"
git push heroku master
```

Or via git:
```cmd
git revert HEAD
git push heroku master
```

---

## Strategic note

This Sprint is the foundation layer for Sprints 2.14.1 (Market Regime
Recommendations), 2.15+ (broker data integration), and future RICS
compliance work.

By establishing scope honestly now:
- Sprint 2.14.1 can confidently apply regime adjustments knowing the
  user has been shown what asset types Thammen actually claims to value
- Broker data integration can be validated only against `supported`
  tier assets (the only place we make full Sales Comparison claims)
- Future RICS-related Sprints have a clear baseline to build on

The deferral of Sprint 2.14.1 (regime recommendations) until after
broker data arrives is intentional and consistent with the discussion:
**we should not apply specific calibration adjustments until we have
ground truth to validate them against.** Sprint 2.14.0 ships the
**uncertainty disclosure** without the **numerical adjustments** —
honesty without overconfidence.

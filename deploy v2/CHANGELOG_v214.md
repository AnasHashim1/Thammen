# CHANGELOG v214 — Sprint 2.22.0b.143 «إنجليزيّة إفصاحات النطاق» (EN twins for the scope-of-service disclaimers/requires)

**Engine:** `thammen-sprint2p22p0b143-en-scope-disclaimers` · **api-health:** `3.1.0-sprint2.22.0b.143`
**Files:** `en_localize.py` (+9 CATALOG entries) · `evaluate_unified.py` (2 version-string lines) · `test_sprint_2_22_0b143.py` (new) · `test_sprint_2_22_0b142.py` (1 R6/Lesson-2 version-pin re-point).
🟢 **BACKEND COPY-ONLY / VALUE-NEUTRAL** — `api.py` + `index.html` + the valuation engine UNTOUCHED (only the 2 version lines). Additive `_en` only; AR mode byte-identical; amount/method/rule never touched.

## 1. Why this matters
Since the b88 EN reveal, an EN user's **default villa result** still leaked Arabic on the **scope-of-service disclaimer** — a line that renders on **every valued villa** («The valuation of standalone villas uses comparison with MoJ transactions… the effect of internal condition/finishes/view is not taken into account»). It was Arabic in EN mode. b140 already made the result-screen read `pick(ss,'disclaimer')` / `pick(ss,'requires_user_input')`, but the engine `_en` twin was never authored → `pick()` fell back to AR. This is **Sprint B slice 2** of the PO-approved A(b140)→ترشيق(b141)→B EN-completion sequence (b142 = slice 1, the caveat/checklist arrays).

## 2. Root cause
`en_localize.attach_en` fills `{base}_en` from `CATALOG.get(_norm(v))` for constant `_ar` strings. The scope disclaimers/requires ARE constant, but:
- **standalone_villa** disclaimer: the catalog key was «…(نافذة 24 شهراً)…» while the live string is «…(صفقات آخر 24 شهراً)…» → **normalized-key mismatch** → no `_en` → the villa leaked on every valued result.
- **compound_small / tower / palace / commercial / industrial / agricultural** disclaimers + **tower / palace** `requires_user_input`: not in the catalog at all.
- (land / compound_large / apartment / unknown disclaimers + compound_large/apartment requires were already covered.)

## 3. What this patch does
`en_localize.py` — **9 additive CATALOG entries** (all CONSTANT strings, keyed by the exact `_norm`'d Arabic extracted from `scope_of_service._ASSET_SCOPE`):
- 7 disclaimers: standalone_villa (the mismatch variant «صفقات آخر 24 شهراً») · compound_small · tower · palace · commercial · industrial · agricultural.
- 2 requires: tower («…للبرج») · palace («ميزانية البناء الأصلية…»).

The scalar `attach_en` rule then fills `service_scope.disclaimer_en` / `requires_user_input_en` on the response; the b140 `pick(ss,'disclaimer')` / `pick(ss,'requires_user_input')` render them in EN mode. **Frontend UNTOUCHED** (R14 N/A by construction — the existing `pick()` renders the new `_en` identically; the §20.18/b139 backend-only precedent). Locked termbase (MoJ → "Ministry of Justice"; "income approach (Income Approach)"; "Thammen's scope"; straight apostrophes). **Personas:** lawyer APPROVE (each EN faithfully carries its AR scope disclaimer + directs out-of-scope types to specialists — no new claim, no weakened «ليس معتمداً»); linguist APPROVE (register-consistent فصحى → English on the b78 catalog).

## 4. Scope split (Rule #38)
b142 measured the result-screen EN leaks 32→17. Consumption-recon (b139 discipline — don't author `_en` for a DEAD field) reduced the "17" to **5 genuinely-rendered leaks**: (a) scope `disclaimer` + `requires_user_input` [b143], (b) corner + HBU `evidence` [interpolated → engine-emit, **b144**], (c) MUC `factors` [+ `recommendations` — a two-contributor + `UncertaintyLevel`-dataclass + frontend `pickArr` array slice, **b145**]. DEAD on the result screen (skipped, documented): `valuation.method_label`, top-level `valuation.source`, `valuation.geometry.note` (re-authored inline via `t()`), `value_decomposition.land.source`, `trend.reason`, corner `note`. Landmark names already have `_en`. b143 = the scope family = the cleanest single-mechanism (constant → catalog), single-file, frontend-untouched slice; the villa disclaimer is the high-frequency valued-path win.

## 5. Verification — empirical evidence
- **py_compile** OK (`en_localize.py`, `evaluate_unified.py`).
- **Coverage (real code, E14):** ran `scope_to_dict` → `attach_en` for **all 10 distinct scopes + the unknown fallback** → every one gets `disclaimer_en` (+ `requires_user_input_en` where `requires_ar` set); **0 missing**. `_ar` byte-unchanged; `attach_en` never clobbers an engine `_en`.
- **End-to-end on the REAL served b142 Marikh payload:** before → no `disclaimer_en`; after `attach_en` → `disclaimer_en` = "The valuation of standalone villas uses comparison with Ministry of Justice…", `disclaimer_ar` unchanged, `amount` 2,400,000 unchanged.
- **Isolated `test_sprint_2_22_0b143.py` 21/21** (coverage drift-guard · villa main-leak + termbase · the 9 new entries + MoJ-expansion · value-invariance: `_ar` not mutated, no engine-`_en` clobber, `scope_to_dict` + frontend `pick` UNTOUCHED, no b143 marker in index.html · version).
- **DoD:** aggregator **ALL COUNTS MATCH** · security **16/16** · surface honesty **45/45** · broad walk **ALL GREEN** (1 R6/Lesson-2 re-point: b142's exact-version pins → format checks; b142 = 17/17; zero value/security/methodology/compliance assertion weakened).

## 6. Deployment
```
git add en_localize.py evaluate_unified.py test_sprint_2_22_0b143.py test_sprint_2_22_0b142.py CHANGELOG_v214.md docs/Session_Log.md
git commit -m "Sprint 2.22.0b.143 «إنجليزيّة إفصاحات النطاق» (EN twins — scope disclaimers/requires)"
git push origin master
git subtree push --prefix "deploy v2" heroku master
```

## 7. Verification curl (post-deploy)
```
curl -s https://thammen.qa/api/health | findstr b143
curl -s -A "Mozilla/5.0" -X POST https://thammen.qa/api/evaluate -H "Content-Type: application/json" -d "{\"zone\":54,\"street\":541,\"building\":6}" | findstr disclaimer_en
```
Expect: health = b143 · the villa response now carries `service_scope.disclaimer_en` (English) + `disclaimer_ar` unchanged + `amount` 2,400,000 · the 5-fixture value byte-gate byte-identical to v306.

## 8. What's NOT in this patch (scope boundary)
- **b144** = geometric-findings EN (corner + HBU `evidence_en`) — interpolated → engine-emit in `geometric_factors.py` + a `geo_section` copy at `evaluate_unified.py:7285/7300` (the rebuild copies only `evidence_ar` today) + R14 on the Geometric Findings card.
- **b145** = MUC `factors` + `recommendations` EN — two contributors (`assess_uncertainty` + `evaluate_unified.py:4893`) through the `UncertaintyLevel` dataclass + a frontend `pickArr` swap (`c.factors.forEach` @4450).
- No value/methodology/data change; no engine builder or frontend touch; the DEAD result-screen fields (method_label, valuation.source, geometry.note, land.source, trend.reason, corner note) stay AR by design (not rendered).

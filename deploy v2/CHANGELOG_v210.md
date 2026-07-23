# CHANGELOG v210 — Sprint 2.22.0b.139 «إنجليزيّة الملحق المتخصّص (توائم خلفيّة)» (audience-brief backend EN twins)

**Engine:** `thammen-sprint2p22p0b139-en-brief-backend-twins` · **SPRINT_TAG** `2.22.0b.139` · api-health `3.1.0-sprint2.22.0b.139`
**Date:** 2026-07-23 · **Files:** `evaluate_unified.py` · `market_position.py` · `api.py` · `output_briefs.py` · `stock_strata.py` · `test_sprint_2_22_0b139.py` (new)
**Class:** 🟢 BACKEND COPY-ONLY / **VALUE-INVARIANT** — additive `{base}_en` twins only; `index.html` UNTOUCHED → the AR default is byte-identical and R14 is N/A by construction (§20.18 / b84–b87 precedent).

---

## 1. Why this matters

The EN reveal shipped at b88 and the always-visible engine note bodies were completed at b117; b138 did the result-screen frontend fossils. The **audience-brief (renderSection) specialist surface** still fell back to Arabic in EN mode on the engine-authored fields that carry an **interpolated number** (a `%`, an `n=`, a `+N%`) — because the b78 `en_localize` constant catalog (`attach_en`, `en_localize.py`) can only translate *constant* strings and, per its own docstring, "number-interpolated strings … get site-level `_en` twins in a later slice." b139 is that slice: an EN user reading the report's income cross-check, sensitivity table, market-position section, or the strata land reference saw those interpolated labels in Arabic.

## 2. Root cause

The interpolated engine fields are emitted with only an `{base}_ar`. The frontend already `pick()`s every one of these bases (e.g. `index.html` 4259 `cap_rate_label`, 4274 `delta_label`, 4350 `description`, 4324 `rent_source`, 4266 `role`, 2176 brief `muc_basis`), so `pick()` returns the `_ar` in EN mode whenever the `_en` twin is absent. The catalog cannot help (the value varies), so the twin must be authored at the emission site.

## 3. What this patch does (backend `_en` twins, auto-rendered via existing `pick()`)

- **income `cap_rate_label`** — the `_en` twin at all 3 emission sites (income cross-check, fast-income brief, fast-income response) + forwarded through **both** passthrough builders (investor-brief-from-income + the main `income_approach` response). Calibrated → "Calibrated capitalization rate {%}% (sample n={N}, {conf})"; typical → "Capitalization rate {%}% (typical …)". `_ar`/`_en` full parity (every site interpolated).
- **income `rent_source`** — the interpolated variants twinned: municipal "Municipality median (n={N})", area-median "Area rent median (n={N}, confidence={conf})", cap-estimate "Estimated from a typical capitalization rate ({%}%) — no actual rent data for the area". The constant "إفادة العميل (الإيجار الفعلي)" is catalog-covered (attach_en) — **not** a site twin. Forwarded through both passthrough builders.
- **income `role`** — the 3 non-cataloged sites twinned (T2 "Apartment sale listings — Lusail"; brief "Adopted primary value for this asset class …"; response "Adopted primary value"). The "تأكيد منهجي …" / "القيمة الأساسية المعتمدة" constants stay catalog-covered — **never** a `None` passthrough (which would block the catalog, `en_localize.py:184`).
- **scenario `delta_label`** — `_en` at all 3 sensitivity sites ("Base" / "+N%"). Full parity.
- **market-position `description`** — new `MarketPosition.description_en` field + `_describe_position_en` (7-branch mirror of `_describe_position_ar`, interpolated gap%/n) + emit in `to_dict` + both compute paths; the income-path market description (evaluate_unified) gets `position_en` + `description_en`; `api.py` forwards `description_en` on both response branches.
- **brief `muc_basis` / `muc_review_recommendation`** — `output_briefs.py` now copies the root `muc_basis_en`/`muc_review_recommendation_en` (authored b117) into the buyer + valuer brief MU sections.
- **strata `land_reference.source`** — the constant `source_en` "Median of registered land-sale transactions in the same district (MoJ)".

**Deferred to b140 (#42):** the frontend renderSection literal sweep + scope-disclaimer (direct render, `index.html:3671`) + STATUS_AR/FRESHNESS_AR LANG-switch + geometry/corner/brief-`note` site-twins — all need `index.html` edits (this sprint is backend-only).

## 4. Value-invariance

Purely additive: `git diff --numstat` = `market_position.py +42/-0`, `api.py +2/-0`, `output_briefs.py +4/-0`, `stock_strata.py +1/-0`, `evaluate_unified.py +NN/-2` (the −2 = the two ENGINE_VERSION/SPRINT_TAG lines only). No `_ar`, no valuation logic, no `amount`/`method`/`rule` touched. `index.html` UNTOUCHED. The `en_localize` catalog is untouched. In AR mode `pick()` returns the (unchanged) `_ar` → byte-identical.

## 5. Verification — empirical evidence

- **Recon (measured, Rule #58):** the 8-fixture live b138 surface has only **6** consumed+untranslated base keys (the caches spanning b117→b129 over-reported 43); `trend.reason`/`valuation.source`/`method_label` are dead (not rendered) and skipped; the catalog already covers the constant scope/refusal/methodology strings (they showed `_en` on the LIVE fixtures).
- **market_position functional (E14, real `compute_position`):** all 5 positions + no_benchmark → `description_en` present, no Arabic, `description_ar` intact, `gap_pct` unchanged.
- **Isolated `test_sprint_2_22_0b139.py`: 80/80 PASS** — real `compute_position` + `_describe_position_en` all branches + source-level twin/parity + the passthrough forwards + the "no `None` role_en passthrough" catalog guard + termbase discipline + value-invariance `_ar`-template guard.
- **py_compile** 5/5 OK.
- **DoD:** aggregator **ALL COUNTS MATCH** (395) · security **16/16** · surface-honesty **45/45** · broad walk **ALL GREEN** (b138 190 → 191, +b139 test).
- **Personas:** lawyer + linguist **APPROVE** (descriptive-not-verdict market position; income-as-cross-check honesty; factual MoJ attribution; termbase locked; no new claim / no weakened disclaimer).
- **R14: N/A by construction** — `index.html` git-confirmed UNCHANGED; the frontend `pick()` (proven b80–b83) renders the new `_en` in EN mode identically; the b84–b87/§20.18 backend-only precedent.

## 6. Deployment

```
git push origin master
git subtree push --prefix "deploy v2" heroku master
```
(origin backup first — R1 ritual — then the Heroku production push on the explicit Gate-1 «go».)

## 7. Verification curl (post-deploy)

```
curl -s -A "Mozilla/5.0" https://thammen.qa/api/health   # → 3.1.0-sprint2.22.0b.139
# income villa (54/541/6 + rent) → income_approach.cap_rate_label_en present + 5-fixture value byte-gate byte-identical to v302
```

## 8. What's NOT in this patch

- The frontend renderSection literal sweep, the scope-disclaimer, STATUS/FRESHNESS LANG-switch, and the geometry/corner/brief-`note` site-twins → **b140** (they touch `index.html`).
- The `en_localize` constant catalog (unchanged) and every already-translated field (scope label/reason/methodology, refusal message/recommendation, trend window/suppressed_reason, top-level methodology) — done by b78/b84–b87/b117.
- No valuation/methodology/value change; the S3 consent screen (PDPPL/PO) is separate.

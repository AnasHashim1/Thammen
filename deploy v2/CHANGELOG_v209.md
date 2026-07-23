# CHANGELOG v209 — Sprint 2.22.0b.138 «إنجليزيّة أحافير شاشة النتيجة» (EN result-screen fossils)

- **Engine:** `thammen-sprint2p22p0b138-en-result-fossils` · SPRINT_TAG `2.22.0b.138` · api-health `3.1.0-sprint2.22.0b.138`
- **Date:** 2026-07-23
- **Type:** 🟢 FRONTEND-ONLY / VALUE-NEUTRAL (`index.html` + the 2 version-string lines in `evaluate_unified.py`; `api.py` + the valuation engine UNTOUCHED)
- **Files:** `index.html` · `evaluate_unified.py` (version bump only) · `test_sprint_2_22_0b138.py` (new) · 5 R6/Lesson-2 sibling re-points (`test_sprint_2_22_0b27/b36/b60/b73/b137.py`)

## 1. Why this matters
Since the b88 EN reveal (`EN_ENABLED=true`), an English user's **default landing = the result screen** still rendered **hardcoded Arabic** on ~15 dynamic surfaces: the re-evaluation alerts/toasts, the fpHint setbacks line, the classification/land-reality/shared-plot alerts, the geometry card, the range-expansion note, the market-trend card, the auto-detected-landmarks card, location features, known-unknowns, the verify link, and the buyer financing unit. These are hardcoded string literals — not translated by the `t()`/`pick()` i18n layer — so they showed Arabic in EN. Partial-EN is the exact defect being closed.

## 2. Recon (measure-first, Rule #58)
The carried-forward «fossils show()» list (§20.111, b83-era) was stale — b84–b87/b88/b117 closed much of the backend `_en` track since. Two parallel read-only agents **measured the live b137** surfaces: (a) frontend fossils (Arabic literals outside `t()`) = ~55 sites, all in `show()` + the re-eval helpers; (b) backend `_en` gaps (fields read via `pick()` with no `_en` twin) = a separate list. b138 fixes **(a) only** (frontend, no engine); (b) + `renderSection` + the data-`_ar` reads = the queued **b139**.

## 3. What this patch does
Every hardcoded Arabic literal in the result-screen render path → `t('<AR-verbatim>','<EN>')`. Because `t(ar,en)` returns `ar` when the UI is Arabic (the default), **AR mode is byte-identical**; EN mode renders the English arg. The HTML wrapper is kept OUTSIDE each `t()` arg (only the Arabic text is wrapped), so EN args stay clean. ~57 sites across: `thammenReEvalOverride`/`…FromInput`/`thammenReEvalGeometry` (5) · fpHint · the a8 methodology accordion label · subtype/zoning-mismatch + asset-type-reality + multi-QARS alerts · the UX3 not-supported line + «يتطلب» label · the geometry card (max-buildable / confirmed / shared / cap-fallback / default + buttons + basement note) · the building-details notice · range-expansion · trend (headlines + the `title` tooltip `ر.ق/م²`/`معاملة`) · geometric-findings (title + `مساحة محقّقة من Cadastre` + walkable/mixed/unit tags) · location-features title · known-unknowns title · the verify-link · the financing-calc `ر.ق/شهر` unit. **Value-neutral by construction** — no `amount`/`low`/`high`/`method`/`rule` touched; the engine + `api.py` are untouched (only the 2 version lines).

## 4. Personas (standing PO directive)
- **Linguist APPROVE** — EN register-consistent with the b78 catalog (QAR, valuation, capitalization rate, Ministry of Justice); no apostrophes (the b80/b81 typographic nit avoided).
- **Lawyer APPROVE** — the compliance-adjacent strings (verify link, «not certified»-adjacent notices, the setbacks/coverage disclosures) carry every AR claim faithfully into EN with no new claim and no weakened disclaimer; value-neutral.
- No value/methodology change → no RICS-valuer gate; no data/privacy → no privacy persona.

## 5. Verification — empirical evidence
- **node --check** on the 3 inline `<script>` blocks (main = 291,773 chars) → **all OK**.
- **Completeness scan** (comment-stripped, `show()`+re-eval region): **0 unwrapped Arabic display literals** beyond 4 known-safe false-positives (2 = the `tr.label` CSS-classifier regex; 2 = already-localized `t()`-arg concatenations).
- **Isolated** `test_sprint_2_22_0b138.py` **65/65** (every fossil wrapped with the AR arg verbatim + bare pre-wrap forms gone + i18n infra intact + `api.py` untouched + the embedded completeness guard).
- **DoD:** aggregator **395/395 MATCH** · security **16/16** · surface-honesty **45/45** · broad walk **190/190 ALL FILES GREEN** (189→190). **6 R6/Lesson-2 sibling re-points** (a3 surface-honesty trend-framing pin `trHeadline='اتجاه تاريخي: '`→`t('…'` · b27 setbacks-equation `?'`→`?t('` · b36 `<strong>يتطلب:</strong>`→wrapped · b60 A5 recommendation label→wrapped [was matching the szm occurrence] · b73 cap-note/assumes-typical color pins→wrapped · b137 exact-version pin→b-series format) — every one test-only, the AR arg verbatim, **zero value/security/methodology assertion weakened**.
- **R14 real-Chromium 390×844** (served static + the live `.basket/f_marikh.json` + synthetic alert/UX3 payloads): **AR** → value **٢٬٤٠٠٬٠٠٠** byte-identical, geometry/trend(+`ر.ق/م²`/`معاملة`)/findings/location/unknowns/verify all Arabic, **0 EN leak**, no overflow (rOut 370<390). **EN** (`dir=ltr`) → all those surfaces + mqr/szm/atr/UX3 render **English**, **0 AR-label leak**, value byte-identical, no overflow; the injected `message_ar` correctly stays Arabic (the b139-scope data field). **0 console errors** across every render.

## 6. Deployment
```
cd /d "C:\Thammen"
git add "deploy v2/index.html" "deploy v2/evaluate_unified.py" "deploy v2/test_sprint_2_22_0b138.py" "deploy v2/test_sprint_2_22_0b27.py" "deploy v2/test_sprint_2_22_0b36.py" "deploy v2/test_sprint_2_22_0b60.py" "deploy v2/test_sprint_2_22_0b73.py" "deploy v2/test_sprint_2_22_0b137.py" "deploy v2/test_sprint_2p22p0a3_surface_honesty.py" "deploy v2/CHANGELOG_v209.md"
git commit -m "Sprint 2.22.0b.138 «إنجليزيّة أحافير شاشة النتيجة»: ~57 result-screen Arabic literals -> t() (frontend, value-neutral); +5 R6/Lesson-2 re-points"
git push origin master
git subtree push --prefix "deploy v2" heroku master
```
(origin FIRST, then the slow subtree split — §20.112 lesson.)

## 7. Verification curl (post-deploy)
```
curl -s -A "Mozilla/5.0" https://thammen.qa/api/health | grep -o '"version":"[^"]*"'
# -> "version":"3.1.0-sprint2.22.0b.138"
# + 5-fixture value byte-gate identical to v301 (54/541/6 2.4M cost_led · 56/647/6 3.8M geo_full ·
#   55/296/13 2.6M e25 · 56/565/21 2.4M matched · 52/903/90 refusal)
# + served index.html carries t('قطعة مشتركة (' / t('اتجاه السوق: ' / t('ما اكتشفه النظام آلياً' / t(' ر.ق/شهر'
```

## 8. What's NOT in this patch (→ b139)
The data-field `_ar` reads that bypass `pick()` (szm/atr/ss `message_ar`/`requires_user_input_ar`/`disclaimer_ar`, `tr.label`/`historical_window_ar`, landmark `name_ar`, corner/HBU `evidence_ar`, `location_features` label, `known_unknowns`, `data_freshness.caveat_ar`, the top-level `disclaimer`) + the missing backend `_en` twins they need (`role`/`rent_source`/`cap_rate_label`/`delta_label`/`methodology`/`reason`/`recommendation`/scope-of-service `label`/`reason`/`requires_user_input`/land-grid `note`/market-position `description`/…) + the `renderSection` audience-brief sweep. The `tr.label` CSS-classifier regex (locale-logic, not display) is intentionally left. The whole-app scan reported 86 Arabic literals outside `t()` — mostly the region false-positives + these other-function b139-scope items.

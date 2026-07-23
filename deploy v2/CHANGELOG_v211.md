# CHANGELOG v211 — Sprint 2.22.0b.140 «الأحافير الإنجليزية المرئية» (visible EN fossils)

**Engine:** `thammen-sprint2p22p0b140-en-visible-fossils` · **api-health** `3.1.0-sprint2.22.0b.140`
**Date:** 2026-07-23 · **Files:** `index.html` (65 lines), `evaluate_unified.py` (2 version-string lines only), `test_sprint_2_22_0b140.py` (new), + 7 R6/Lesson-2 sibling re-points.
**Class:** 🟢 FRONTEND-ONLY / VALUE-NEUTRAL — `api.py` + the valuation engine UNTOUCHED; the 5-fixture value byte-gate is byte-identical by construction. AR default is byte-identical (`t()` returns its AR arg / `pick()` returns `_ar` in AR mode).

## 1. Why this matters
Since the b88 EN reveal, the English version leaked Arabic on prominent surfaces. A full-site review (3 code agents + a live EN walk) measured it: the **`copyResult()` clipboard artifact was 100% hardcoded Arabic** (the doc claim that b138 wrapped it was false — #58), and several **always-visible raw `_ar` reads** ignored an existing `_en`/catalog twin. This is the first of the two-part EN completion (A = visible frontend fossils; B = the engine `_en` twins for the note-body arrays).

## 2. Root cause
`copyResult()` (`index.html:2118-2156`) built every line as a bare Arabic string, no `t()`. Separately, raw `_ar` reads bypassed `pick()` even where the twin exists: `rics_methodology_note_ar` (@3563, twin @evaluate_unified:6921), `service_scope.disclaimer_ar` (@3671, catalog-covered), `requires_user_input_ar` (@3670), `data_freshness.caveat_ar` (@4141, cf. @2668 which already used pick), landmark `name_ar` (@4066/70/74, `name_en` @geometric_factors:559), corner/HBU `evidence_ar` (@4054/60), trend `historical_window_ar` (@4031). The trend label (`tr.label`) had no localization map. The cap-rate gloss (@4258) was a hardcoded Arabic literal. Also a latent bug: `if(d.methodology_ar)lines.push('');lines.push('المنهجية: '+…)` — the `if` guarded only the blank line, so `المنهجية: undefined` was pushed on refusals.

## 3. What this patch does
- **`copyResult()`** fully wrapped in `t()` (labels) + `pick()` (methodology / reason / latest_record) + `ASSET_EN` (asset label) + the `المنهجية` block re-braced so it is fully guarded (the "undefined" bug fixed). In EN the whole artifact is now English except the area name (a proper noun).
- **`pick()` swaps** for fields whose twin/catalog already exists: rics note, scope disclaimer, `requires_user_input`, freshness caveat, landmark `name`, corner/HBU `evidence`, trend `historical_window` — AR byte-identical; EN localizes wherever `attach_en`/the engine set the `_en` (scope disclaimer + interpolated corner evidence remain AR until B adds their catalog/twin — no regression, prepped).
- **`TREND_LABEL_EN` map + `trLabel()`** localize the raw trend label (Rising/Falling/Stable/Volatile/Undetermined); the color regex still keys on the Arabic label.
- **cap-rate gloss** @4258 wrapped in `t()`.

## 4. Verification — empirical
- Isolated `test_sprint_2_22_0b140.py` **42/42**.
- DoD: aggregator **ALL COUNTS MATCH** · security **16/16** · surface honesty **45/45** · broad walk **192/192 ALL GREEN** (191→192; **7 R6/Lesson-2 re-points** — b139 version pin · b30 copy honesty regex · b36 disclaimer-in-else · b15 caveat-foot + the `2p22p0b14`⊂`2p22p0b140` substring collision · b3 copy range line · b54 copy value line · a4 Layer-E render hook — **zero value/security/methodology/compliance assertion weakened**; each AR literal survives as the `t()` first-arg / `pick()` still renders `_ar`).
- py_compile OK · `node --check` on all 3 inline scripts OK.
- **R14 real-Chromium 375** on the live b139 Marikh payload: **AR byte-identical** (copy artifact + result + report render Arabic, dir=rtl) · **EN localized** (`copyResult` fully English bar the area name; methodology / caveat / latest-record / rics-note / landmark-names / trend-label / cap-rate all localized) · **0 console errors** · **no overflow** (375==375) · dir flips rtl↔ltr. The EN residual = exactly the known Sprint-B engine content (known-unknowns list, due-diligence questions, MUC basis, service-charge factor, scope disclaimer [catalog mismatch], interpolated corner evidence, location features, permitted-height, rics-compliance line).
- Personas: **lawyer APPROVE** (EN copy carries the «not a certified valuation» disclosure + verify link — raises defensibility; locked termbase) · **linguist APPROVE** (register-consistent; «غير محدد»→"Undetermined" a deliberate trend-context choice).

## 5. Deployment
`git push origin master` (backup first) → `git subtree push --prefix "deploy v2" heroku master` (from the repo toplevel `C:/Thammen`, Rule #43).

## 6. Verification curl (post-deploy, browser-UA #61)
`curl -s -A "Mozilla/5.0" https://thammen.qa/api/health` → `3.1.0-sprint2.22.0b.140`; served `index.html` carries `var TREND_LABEL_EN=` + `t('قيمة التقييم السوقي: ','Market valuation: ')` + `pick(d,'rics_methodology_note')`; the 5-fixture value byte-gate byte-identical to v303.

## 7. What's NOT in this patch (→ Sprint B, backend `_en` + declutter next)
The engine note-body arrays/notes that need `_en` twins: known-unknowns, due-diligence questions, MUC basis (interpolated n), the b14 service-charge factor, scope-disclaimer catalog entry (value mismatch), interpolated corner `evidence_en`, `historical_window_en`/`suppressed_reason_en`, substantiality `rationale`/`methodology_note`, freshness `banner_en`/`subtitle_en`, location-feature `.label` bilingual key, the `requires` key fix. Per the approved sequence: **A (this) → result-screen declutter → B (backend twins)**.

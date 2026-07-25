# CHANGELOG v217 — Sprint 2.22.0b.146 «التسريبات عارية-المفتاح» (the bare-key + bypass EN leaks the adversarial panel caught)

**Engine:** `thammen-sprint2p22p0b146-en-bare-key-leaks` · **api-health:** `3.1.0-sprint2.22.0b.146`
**Files:** `en_localize.py` (+12 CATALOG entries [BOTH live disclaimer variants · 3 accuracy labels · 6 location labels] + 3 `_TEMPLATES` [window_label n=X · private-residential zone(+suffix) · permitted-height] + `_BARE_EN_KEYS` + the bare-key branch in `attach_en`) · `index.html` (`pickBare()` + 4 bare-key swaps + the A5 pick-bypass fix + the land-grid role pick + the generic-dump `_en` guard) · `evaluate_unified.py` (the 2 version lines) · `test_sprint_2_22_0b146.py` (new).
🟢 **BACKEND-COPY + frontend read-fixes / VALUE-NEUTRAL** — `api.py` + the valuation engine UNTOUCHED; additive `_en` only; bare AR values untouched; amount/method/rule untouched.

## 1. Why this matters — the adversarial panel earned its keep
The b145 ultracode **4-lens verification workflow**: linguist/lawyer/invariance APPROVE (weakened=false), but the **completeness critic REJECTED** the "sequence complete" claim — it found a class **invisible to every prior sweep**: fields whose Arabic lives under a **BARE key** (no `_ar` suffix), which the `_ar`-scan, the scalar catalog rule, AND the b142 leak measurement's follow-up recon all structurally missed. Verified real (each file:line confirmed):
- **`d.disclaimer`** — the compliance-foot disclaimer, raw on **EVERY result** (:4148).
- **`accuracy.label`** — the hero confidence meter, raw on every valued result (:3805).
- **`location_features[].label`** — the «مميزات الموقع» card, raw on every valued villa (:4100).
- **`comparables.window_label`** — the interpolated evidence-header meta on matched-market (:2524).
- Plus: the A5 `recommendation_ar` pick-BYPASS (the `_en` twin existed since b78 — pure frontend miss), the land-grid `role_ar` raw read (`role_en` exists since b139), and a **b142 side-effect** — the valuer trace generic dump rendered BOTH `known_unknowns` AND `known_unknowns_en` (a visible double-render).

## 2. What this patch does
- `en_localize.py`: **`_BARE_EN_KEYS = ('disclaimer','label','window_label')`** + a bare-key branch in `attach_en` (str + `{k}_en` absent + resolvable via `_item_en` → emit `{k}_en`; resolvability-gated so the generic `label` key is safe; never clobbers the b23 scenarios' engine `label_en`). CATALOG += **both live disclaimer variants** (the 3-sentence main-path + the 2-sentence fast-path — measured from the live fixtures; the emit-site constant alone did NOT match, caught by the fixtures run) + `شواهد محدودة`/`تقدير تقريبي`/`بيانات غير كافية` + the 6 uncataloged location labels. `_TEMPLATES` += the window_label shape (`{n36} معاملة، منها {n24} خلال 24 شهراً`) + `منطقة سكنية خاصة ({zone})[-suffix]` + `ارتفاع مسموح: {latin}`.
- `index.html`: **`pickBare(o,k)`** (bare-key sibling of pick/pickArr) + the 4 swaps + `pick(d.refusal_reason,'recommendation')` (A5) + `pick(s,'role')||s.source` (land grid) + the generic-dump guard (`_en` keys never dumped under their own name; the value is PICKED per LANG under the clean key — fixes the double-render AND localizes the valuer trace dump in EN).

## 3. Verification — empirical evidence
- py_compile OK · `node --check` ×3 OK · isolated `test_sprint_2_22_0b146.py` **26/26** (both disclaimer variants + the 3 labels + the templates incl. the `(R1)-TYP` suffix case [caught by the test — the first template missed it] + unresolvable-no-fire + clobber-guard + **all 5 LIVE fixtures resolve with amounts unchanged** + live villa 7/7 location labels + every frontend swap + the dump guard).
- DoD: aggregator **ALL COUNTS MATCH** · security **16/16** · surface **45/45** · siblings b142 17/17 + b145 26/26 · **broad walk 198 files ALL GREEN** — with **4 R6/Lesson-2 re-points** (test-only, zero assertion weakened; each pinned the pre-b146 raw read that b146 made bilingual): `test_sprint_2_22_0b38.py` E6 (`_cmp.window_label` → `pickBare(_cmp,'window_label')` — still surfaced) · `test_sprint_2_22_0b60.py` (A5 recommendation `d.refusal_reason.recommendation_ar` → `pick(d.refusal_reason,'recommendation')` — the AR twin still drives the render) · `test_sprint_2_22_0b15.py` (disclaimer-card literal → the `pickBare(d,'disclaimer')` form — same card/placement) · `test_sprint_2_22_0b124.py` (the «bare acc.label, NOT pick (no twin)» pin — its rationale is exactly what b146 retired; → `pickBare(acc,'label')`).
- **R14 real-Chromium 390×844**: AR — disclaimer/label/location Arabic, 0 EN leak, no overflow; EN — the FULL protective disclaimer ("…a certified valuer is required") + "Limited evidence" + the location labels English, ZERO AR leak, **no known-unknowns double-render** (the dump guard), amount 2,400,000; AR restore byte-identical; **0 console errors**.

## 4. Deployment
origin FIRST → `git subtree push --prefix "deploy v2" heroku master`.

## 5. What's NOT in this patch (→ the specified b147, documented)
The panel's remaining path-specific residuals: refusal `next_steps.options_ar` (an `_ar`-suffixed ARRAY — needs an `*_ar`-array rule variant) · the A11 `szm` fields (message/data_age_note/recommendation — the RARE stale-subtype path, no twins yet) · `rent_reference.caveats_ar` + `investment_scenarios` note/label + the seller/valuer bare residuals (specialist brief sections). No value/methodology change anywhere.

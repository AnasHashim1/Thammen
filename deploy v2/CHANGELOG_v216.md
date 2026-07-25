# CHANGELOG v216 — Sprint 2.22.0b.145 «إنجليزيّة عوامل وتوصيات التحفّظ» (EN twins for the MUC factors/recommendations arrays)

**Engine:** `thammen-sprint2p22p0b145-en-muc-factor-arrays` · **api-health:** `3.1.0-sprint2.22.0b.145`
**Files:** `en_localize.py` (+16 CATALOG constants + a `_TEMPLATES` regex table + `_item_en` + the array rule extended to `factors`/`recommendations`) · `index.html` (2 `pickArr` swaps in the renderSection MU case) · `evaluate_unified.py` (the 2 version lines) · `test_sprint_2_22_0b145.py` (new).
🟢 **BACKEND-COPY + 2 frontend read-swaps / VALUE-NEUTRAL** — `api.py` + the valuation engine UNTOUCHED; additive `_en` arrays only; the `_ar` arrays byte-identical; the render decision still reads the AR array; amount/method/rule untouched.

## 1. Why this matters
The brief **material_uncertainty section** (rendered on the result screen inside the brief fold) listed `c.factors` / `c.recommendations` raw — in EN mode the uncertainty **disclosures** («لم يتم فحص العقار ميدانياً…», «اعتمد النطاق المعروض لا الرقم المفرد», the RICS-compliance recommendation) stayed Arabic. This was the LAST rendered result-screen EN leak (Sprint B slice 4 — after b142 arrays · b143 scope · b144 geometric).

## 2. Root cause + the recon reshape (Rule #58/#38)
The §20.140 pointer anticipated a `UncertaintyLevel`-dataclass threading slice. The recon overturned it: the factors are **MUTATED at 3 post-assembly engine sites** (`:4900` building-unknown `insert(0)` · `:7401` the interpolated widening REPLACEMENT `n={effective_n}` · `:7616` the dispersion append) — parallel-list threading through the dataclass would be alignment-fragile and would still miss those sites. Also measured: the **fast/refusal path carries NO factors arrays** (single-path), the **brief MU content is a pre-mutation COPY** of the root arrays, and MUC's own `known_unknowns` are **unrendered** (skipped, b139). The robust architecture = extend the **en_localize array rule**: the `api.py:262` `attach_en` post-pass sees the FINAL mutated arrays → per-item mapping → index alignment can never drift, and both root + brief copies localize independently.

## 3. What this patch does
- `en_localize.py`: `_ARR_EN_KEYS` += `factors`, `recommendations` · **+16 CATALOG constants** (10 factors + 6 recommendations, incl. the 3 engine-site literals) · a **`_TEMPLATES`** regex table for the 5 NUMBER-INTERPOLATED factor shapes (`n=X` MoJ-sample tiers · rental-data · the widening replacement) · `_item_en(norm)` = catalog-or-template lookup (array items only — the scalar rule untouched). Unresolvable items fall back to the Arabic item (aligned).
- `index.html`: the renderSection MU case renders `pickArr(c,'factors')` / `pickArr(c,'recommendations')` (the guards still read the AR array — the render decision unchanged).

## 4. Verification — empirical evidence
- py_compile OK · `node --check` on all 3 inline scripts OK.
- Isolated `test_sprint_2_22_0b145.py` **26/26**: the COVERAGE drift-guard — a **90-case matrix** over the REAL `assess_uncertainty` (3 asset types × 5 moj_n × 2 rent_n × 3 service-charge) emits 12 distinct factors, **every one resolves** (catalog or template) + the 3 evaluate_unified site literals + the :4909 recommendation · attach_en on a REAL UncertaintyLevel → index-aligned fully-English twins, interpolated `n=15` survives, `_ar` untouched · the LIVE r1 fixture's 5 factors ALL resolve · b142 semantics preserved + all-unresolvable arrays don't fire + never clobbers an engine `_en` + mixed-array fallback aligned · the 2 frontend swaps + guards.
- DoD: aggregator **ALL COUNTS MATCH** · security **16/16** · surface **45/45** · b142 17/17 · b143 21/21 · b144 24/24 · broad walk ALL GREEN.
- **R14 real-Chromium 390×844** (the live r1 payload enriched by the REAL attach_en): **AR** — factors + recommendations Arabic, 0 EN leak, amount ٢٬٤٠٠٬٠٠٠, no overflow; **EN** — dir=ltr, "The Ministry of Justice sample is reasonable but below the ideal threshold **(n=15)**" + "The property has not been inspected in the field — a desktop valuation only" + "A field inspection before making a buy/sell decision" + the full RICS-compliance recommendation render, ZERO AR leak, amount 2,400,000; **AR restore byte-identical**; **0 console errors**. (An initial false-negative was a browser-CACHED index.html — cache-busted reload proved the swap; the fixture's brief copy correctly differs from root [pre-insert snapshot], each localizes independently.)
- Personas: lawyer APPROVE (every uncertainty disclosure carried faithfully into EN — «rely on the displayed range, not the single figure», the desktop-valuation caveat, the full RICS citation; no new claim; raises EN transparency); linguist APPROVE (b78 termbase; straight apostrophes).

## 5. Deployment
origin FIRST → `git subtree push --prefix "deploy v2" heroku master`.

## 6. Verification curl (post-deploy)
`/api/health` = b145 · the 5-fixture value byte-gate byte-identical · the villa response carries `material_uncertainty.factors_en` (English, aligned) + the brief MU content `factors_en`.

## 7. What's NOT in this patch
MUC's own `known_unknowns` array (unrendered — skipped per the b139 dead-field discipline) · the `:7420` banner_ar recompute (not flagged in the b142 leak measurement — out of scope) · no value/methodology change. **With b145 the result-screen EN-completion sequence (b140→b145) is COMPLETE** — all 5 genuinely-rendered leaks closed.

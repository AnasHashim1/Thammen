# CHANGELOG v161 — Sprint 2.22.0b.80 «ربط التقرير المختصر بالإنجليزية» (EN wiring — the short report)

> Engine `thammen-sprint2p22p0b80-en-shortreport-wiring` · SPRINT_TAG `2.22.0b.80` ·
> api-health `3.1.0-sprint2.22.0b.80`. **🟢 FRONTEND-ONLY / VALUE-INVARIANT** — the EN render is
> DORMANT behind `EN_ENABLED` (b77); in AR mode `t()` returns its first (Arabic) arg and `pick()`
> returns the `*_ar` field, so the AR default render is **byte-identical**. `api.py` + the valuation
> engine UNTOUCHED. Files: `index.html` (the `showShortReport` wiring + `ASSET_EN` + the `#srOut`
> LTR CSS), `evaluate_unified.py` (2 version lines), `test_sprint_2_22_0b80.py` (new),
> + R6 re-points on b17/b25/b29/b54/b57/b63, `CHANGELOG_v161.md`. **Fourth sprint of the
> EN-localization track — the first result-family screen rendered in English.**

## 1. Why this matters

b77 = the i18n infrastructure; b78 = the backend EN catalog (`*_en`); b79 = the **core flow**
(gate / home / form / top-bars / scope) rendered in English. b79 left the result + report screens
RTL/Arabic. b80 wires the **short report** (`showShortReport`) — the smallest result-family surface
by engine-field count (it reads 4 `*_ar` fields) and the first of the per-function sequence
(short → full report → confirm → result, smallest→largest, each an independent value-invariant
checkpoint). With the flag flipped (reveal sprint), an English owner now gets the full two-page
short report — the headline, the leader story, the three numbers, the practical takeaway, the
cost/decomposition sources, the scenario table, the investor income view, the evidence transparency,
and the §9 legal block — in English. Built DORMANT so the live AR site is unchanged.

## 2. What this patch does

**`showShortReport` wired** — every hardcoded Arabic literal is wrapped `t('<AR>','<EN>')` (the AR
first-arg = the original literal byte-for-byte → AR byte-identical), and the 4 engine `*_ar` reads
become `pick()`:
- `pick(d.refusal_reason,'message')` (refusal line)
- `pick(inc,'rent_source')` (income rent-source qualifier)
- `pick(it,'label')` (scenario labels — the engine already broadcasts `label_en` via
  `SCENARIO_LABELS`, so these render real English)
- `pick(d.cap_rate_provenance,'district')` (cap-rate cell — still `esc()`-wrapped, b57)

`pick()` degrades gracefully to `*_ar` when an `_en` twin is absent — so the three number-bearing
fields without backend twins (`refusal_reason.message`, `rent_source`, `district`) show Arabic in EN
mode until those twins are authored (the separate backend track), with no AR regression.

**`ASSET_EN`** — a new EN asset-label map beside `ASSET_AR` (a `const`, lexically in scope for
`showShortReport`; the AR build never reads it → byte-identical). The property strip uses
`t(ASSET_AR[d.asset_type]||'عقار', ASSET_EN[d.asset_type]||'Property')`.

**`#srOut` LTR dir-flip** — `body.lang-en #srOut{direction:ltr;text-align:left}` flips the short
report (the `#srOut` id beats the base `.thmr{direction:rtl}` on specificity), with scoped
sub-overrides for the value cells (`.thmr-row .v` → right), the scenario table headers
(`.thmr-sctab th` → left, the value column → right), and the cost↔market range-bar dots
(`.thmr-rbar .dot.c/.dot.m` re-anchored from physical `right` to `left`). **Scoped to `#srOut` only**
— the full report (`#repOut`, no `.thmr` class) and the result screen stay RTL in EN mode until
their own sprints (b81/b82/b83).

**Compliance copy (lawyer + linguist personas, the standing PO directive).** The §9 legal block,
the «ليس تقييماً معتمداً» honesty footer, the IFRS 13 / judicial-banking / estate-division
exclusions, the no-liability clause, the forced-sale ×0.90 («not a liquidation valuation») qualifier,
and the CC BY 4.0 MoJ attribution are authored in English **faithful to the Arabic** — no new claim,
no weakened disclaimer; EN terminology matches the shipped catalog (Automated Market Valuation / not
a certified valuation / Ministry of Justice / registered transactions / licensed valuer / field
inspection). **Lawyer: APPROVE** (every AR protection carried; nothing added or weakened).
**Linguist: APPROVE-WITH-NOTE** (فصيح, register- and terminology-consistent; the only nit is a mixed
straight/curly apostrophe style across ~5 possessives — a typographic-consistency item for the
reveal-sprint PO wording pass; cosmetic, dormant, no effect on AR or meaning).

## 3. Verification

- **R14 real-Chromium 390×844** (served `index.html`, the 5 captured fixtures):
  - **AR default (dormant)** — cost-led (Marikh): **10/10** AR markers present, **0** English
    leakage, amount ٢٬٤٠٠٬٠٠٠, `dir=rtl`, no overflow (scrollW 390 == clientW 390, right 370<390).
    AR flip-back across **all 5 branches** (cost/market/income/land/refusal): **0 English leakage**,
    `dir=rtl` restored, `lang-en` removed. **0 console errors.**
  - **Forced EN** (`EN_ENABLED=true; setLang('en')`) — cost-led: **15/15** EN markers (incl. §9
    legal, IFRS 13, "not a certified real-estate valuation", "Standalone villa", scenario table),
    **0** Arabic leakage in the structural copy, `dir=ltr` flip, `.thmr-row .v` right-aligned, no
    overflow (390==390, max-right 370). market (3.8M) / income (2.8M) / land (1.2M) / refusal all
    render, `dir=ltr`, no overflow. The **full report `#repOut` stays `dir=rtl`/Arabic** in EN mode
    (no bleed). **0 console errors** throughout.
- **Isolated** `test_sprint_2_22_0b80.py` **20/20** (`ASSET_EN`; the t()-wiring of the head /
  section titles / number chips; the 4 `pick()` swaps; §9 compliance in BOTH languages + IFRS 13 +
  forced-sale; the `#srOut`-scoped CSS + the NO-bleed guard; EN coverage markers; the verbatim AR
  literals + the b54 locked identity + `EN_ENABLED=false` dormancy).
- **DoD**: aggregator **395/395 MATCH** · security **16/16** · surface **45/45** · broad walk
  **136/136 ALL GREEN** (135→136, +b80). **R6/Lesson-2 re-points (6):** b17 / b25 (×2) / b29 / b54 /
  b57 / b63 pinned the OLD bare-literal/structure of `showShortReport` (e.g. `>التقرير الكامل<`,
  `it.label_ar`, the `<small>` subhead, `esc(...district_ar)`, the `المرجع` header) — each relaxed to
  the new `t()`/`pick()`-wrapped form (the literal itself is unchanged, preserved as the `t()`
  first-arg). **No value / security / methodology assertion weakened.**
- `node --check` N/A (node absent — R14 Chromium is the JS gate; the a8/a21 precedent). The JS
  parsed clean (all functions defined, 0 console).

## 4. Deployment

```
git -C "C:/Thammen" add "deploy v2/index.html" "deploy v2/evaluate_unified.py" \
  "deploy v2/test_sprint_2_22_0b80.py" "deploy v2/test_sprint_2_22_0b17.py" \
  "deploy v2/test_sprint_2_22_0b25.py" "deploy v2/test_sprint_2_22_0b29.py" \
  "deploy v2/test_sprint_2_22_0b54.py" "deploy v2/test_sprint_2_22_0b57.py" \
  "deploy v2/test_sprint_2_22_0b63.py" "deploy v2/CHANGELOG_v161.md"
git -C "C:/Thammen" subtree push --prefix "deploy v2" heroku master
git -C "C:/Thammen" push origin master
```

## 5. Post-deploy verification

```
curl -s https://thammen.qa/api/health    # engine = thammen-sprint2p22p0b80-en-shortreport-wiring
# 5-fixture VALUE byte-gate (browser-UA POST) byte-identical to v248–v251.
# served HTML carries: ASSET_EN · t('ثمّن — التقرير المختصر','Thammen — Short Report')
#   · pick(it,'label') · body.lang-en #srOut{direction:ltr  — and NO lang-en/lang-toggle rendered
#   (the toggle stays dormant behind EN_ENABLED → the live AR short report is byte-identical).
```

## 6. What's NOT in this patch

- **No reveal** — `EN_ENABLED` stays false; the live AR short report is byte-identical (no toggle,
  no `lang-en`). The flag flips only after the remaining result-family screens are wired.
- **Only the short report** — `showReport` (full report, `#repOut`), `showConfirm`, and `show`
  (result screen) are NOT wired here; they keep RTL/Arabic in EN mode (b81/b82/b83). The `#srOut`
  LTR CSS is deliberately scoped so it does NOT bleed into `#repOut` / `#resultsScreen`.
- **Backend `_en` twins for the number-bearing notes** — `refusal_reason.message_ar`,
  `rent_source_ar`, `cap_rate_provenance.district_ar`, and `window_used` have no `_en` twin yet, so
  they render Arabic in EN mode (graceful `pick()` fallback). Authoring those twins is the separate
  backend track.
- **No engine / methodology change** — value-invariant; the 5-fixture VALUE gate is untouched.

## 7. Next

- **b81** — wire `showReport` (the full report, ~21 `*_ar` fields) via `t()`/`pick()` + its own
  `#repOut` LTR overrides + a fresh R14 (the next, larger, function in the sequence).
- then **b82** `showConfirm`, **b83** `show` (the result screen).
- the backend `_en` twins for the number-bearing notes (leadership / cost / sources / freshness).
- **reveal** — flip `EN_ENABLED=true` once the result family is complete (full dual-language R14 +
  the PO wording sign-off, incl. the apostrophe-style normalization the linguist flagged).

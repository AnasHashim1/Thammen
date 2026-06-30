# CHANGELOG v164 — Sprint 2.22.0b.83 «ربط شاشة النتيجة + البُناة المشتركة بالإنجليزية» (EN wiring — the result screen + the 6 shared result-family builders)

**Engine:** `thammen-sprint2p22p0b83-en-result-screen-builders` · **SPRINT_TAG** `2.22.0b.83` · **api-health** `3.1.0-sprint2.22.0b.83`
**Files:** `index.html` (the result screen `show()` + the 6 shared builders + renderSection + scoped CSS) · `evaluate_unified.py` (the 2 version-string lines) · `test_sprint_2_22_0b83.py` (NEW) · 13 sibling test re-points (R6/Lesson-2)
**Class:** 🟢 FRONTEND-ONLY / **VALUE-INVARIANT** — `api.py` + the valuation engine UNTOUCHED; the EN render is DORMANT behind `EN_ENABLED=false` (b77); in AR mode `t()` returns its first (Arabic) arg and `pick()` returns `*_ar`, so the AR live render is byte-identical.

---

## 1. Why this matters

The EN-localization track had wired the three smaller result-family screens — the short report (`#srOut`, b80), the full report (`#repOut`, b81), and the confirmation screen (`#cgOut`, b82). The **result screen** (`show()`, the 721-line screen every owner lands on) plus the **6 shared result-family builders** it owns (`evidencePanelHtml` + `_evidenceRatings`/`_evPill`/`_evOneRow` · `pbRows` · `_decompHtml` · `_substHtml` · `_strataHtml` · `renderSection`) were still Arabic-only. This is the largest single UI surface and the last bilingual gap in the result family. The PO directed the b83 bundle (show + all 6 builders) into ONE session (#39 flag — single-purpose discipline relaxed by explicit PO instruction: «ارجو ان تعمل كل شيء هنا»).

## 2. Root cause

`show()` and the 6 builders emitted hardcoded Arabic literals and read engine `*_ar` fields directly into the DOM. Until they route through the b77 i18n primitives, EN mode (when revealed) would render the result screen in Arabic. (Until the reveal, this is invisible — `EN_ENABLED=false`.)

## 3. What this patch does

**The mechanical contract (AR byte-identical by construction):**
- every hardcoded Arabic literal → `t('<AR-verbatim>','<EN>')` (the AR first arg is the original literal byte-for-byte).
- every `*_ar` *display* read → `pick(obj,'base')` (returns `obj.base_ar` in AR), while every `if(...)` **truthiness guard still reads `.X_ar`** (so the render decision is unchanged).
- new LANG-aware maps where a value is keyed by an AR token: `EV_RATING_EN`, `MUC_LEVEL_EN`, `STATUS_EN`, `FRESHNESS_EN`, plus `posLabels`/`levelLabels` selected by `LANG`. `qarFmt(n)` centralizes the `ر.ق`/`QAR` currency suffix; `fmt()` already locale-switches the digits (b77).
- **renderSection** comparable-grid local `const t=cp.time_pct…` renamed → `const t2=…` to avoid shadowing the global `t()` i18n function.

**The builders (direct edits):** `_evidenceRatings` labels · `_evPill` (rating word via `t(rt,EV_RATING_EN[rt]||rt)` + the «N/A — land» case) · `evidencePanelHtml` title + `pick(acc,'explanation')` · `_evOneRow` · `pbRows` (cadastral/electricity/water/age labels + `pick(b,'vintage_note')`) · `_decompHtml` · `_substHtml` (the `⏳` icon preserved — out of EN scope) · `_strataHtml`.

**show() body (assertion-guarded transform, 74 replacements):** hero label/range · MUC level chip · tier badge · cost-led basis note (b64) + e25 divergence (b72) · all condition/teardown/luxury/leadership/hbu/old-stock notes via `pick` · the buyer financing calculator · the not-certified TIER-1 line · the two TIER-2 accordion titles · keystone + considered comparables · the refusal path (h2 + facts + CTA) · the asset label via `t(ASSET_AR,ASSET_EN)`.

**renderSection (assertion-guarded transform, 108 replacements):** ~50 `row()` labels · `posLabels`/`levelLabels` · `STATUS_EN`/`FRESHNESS_EN` · `pick()` content + section title.

**Scoped CSS (dir-flip, the b80/b81/b82 pattern):** `body.lang-en #rOut{direction:ltr;text-align:left}` + `body.lang-en #rOut .rhero{text-align:center}` (the navy hero stays centered) + a few left-align overrides for `.br-l`/`.rl`/`.ev1lbl`. Scoped to `#rOut` — the prior `#srOut`/`#repOut`/`#cgOut` blocks are intact and there is no global `.thmr` flip.

## 4. Verification — empirical evidence

- **Isolated** `test_sprint_2_22_0b83.py` **39/39** (E14 — reads the real `index.html` + `evaluate_unified.py`: the LANG maps, all 6 builders, the show() body, the scoped CSS, the value-invariance contract [AR verbatim kept + no bare `*_ar` insertion remains + the truthiness guards still read `.*_ar` + `_srPayment`/the b3 range marker present], and the engine bump).
- **13 sibling R6/Lesson-2 re-points** (the now-wrapped literals): b3, b15, b31, b32, b34, b35, b37, b52, b54, b57, b58, b60, b77 — intent preserved, **zero value/security/methodology assertion weakened** (the AR string stays inside the `t()`/`pick()` arg).
- **node --check** on the extracted inline JS = **OK** (the ~250 wiring sites parse clean).
- **DoD:** aggregator `run_sprint_2p22p0a_suite.py` **395/395 (MATCH)** · security **16/16** · surface **45/45** · broad walk `2p22p0_pre/run_regression_2p22p0a.py` **139/139 ALL GREEN** (138.3s).
- **R14 real-Chromium 390×844** (server `thammen-static`, 4 fixtures × 2 modes):
  - **Marikh cost-led** — AR: amount **2,400,000**, hero «التقييم السوقي» / «٢٬٤٠٠٬٠٠٠ ر.ق», all AR markers, **0 EN-chrome leak**, dir=rtl, no overflow. EN (forced `LANG='en'`+`lang-en`): amount **2,400,000**, hero "Market valuation" / "2,400,000 QAR", all 6 EN chrome strings, `#rOut` dir=ltr, hero centered, no overflow.
  - **V001 market-led** — AR 3,800,000 / «٣٬٨٠٠٬٠٠٠ ر.ق» no EN-leak; EN 3,800,000 / "3,800,000 QAR" EN chrome, **no AR-chrome leak**, dir-flip, no overflow.
  - **apartment refusal** (amount null) + **raw_land** (1,200,000) — both render cleanly AR+EN, no overflow, value-invariant.
  - **0 console errors/warnings** across all renders.

**Value-invariance:** the value axis is byte-identical in BOTH modes (2.4M / 3.8M / null / 1.2M); `api.py` + the engine are untouched; the live 5-fixture value byte-gate is unaffected.

## 5. Deployment

```
git -C "C:/Thammen" subtree push --prefix "deploy v2" heroku master
git push origin master
```

## 6. Verification curl (post-deploy)

```
curl --compressed -s https://thammen.qa/api/health    # engine = …b83
curl --compressed -s -X POST https://thammen.qa/api/evaluate -H "Content-Type: application/json" \
  -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120 Safari/537.36" \
  -d '{"zone":54,"street":541,"building":6}'           # cost_led 2,400,000 (byte-identical)
```
Served `index.html` carries `body.lang-en #rOut{direction:ltr` + `var EV_RATING_EN=` + `function qarFmt(` + `const t2=cp.time_pct`; `class="lang-en"` rendered = 0 (EN dormant).

## 7. What's NOT in this patch (carried forward, Rule #42)

- **Backend `_en` twins** for the number-bearing engine NOTE bodies (leadership / cost / condition / age / hbu / scenarios / methodology / rics-note / reason / MUC clause / freshness / window_used) — `pick()` falls back to AR for these until they land (the separate backend track; the result-screen CHROME [labels/titles] is fully EN now, the engine-authored note BODIES are the remainder).
- The `⏳` emoji in `_substHtml` (out of EN scope — a separate follow-up).
- The **reveal** sprint: flip `EN_ENABLED=true` + the PO wording sign-off + the straight-vs-curly apostrophe normalization noted by the linguist persona in b80/b81.
- No methodology / value / security change — frontend i18n wiring only.

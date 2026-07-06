# CHANGELOG v188 — Sprint 2.22.0b.107 «إصلاح 3 أخطاء في واجهة العرض» (S2 — UI bug-fix bundle)

**Engine:** `thammen-sprint2p22p0b107-ui-bugfix-bundle` · **SPRINT_TAG** `2.22.0b.107`
**Date:** 2026-07-06 · **Files:** `index.html`, `evaluate_unified.py` (the 2 version lines) (+ `test_sprint_2_22_0b107.py`)
**Class:** 🟢 FRONTEND / VALUE-INVARIANT — a display key-name fix + EN `t()`-wrapping + modal a11y; no
value/method/rule change (the 5-fixture villa byte-gate holds by construction). `api.py` untouched.
The b64-precedent single-purpose UI-bundle.

---

## 2. Why (3 measured frontend defects surfaced across the audit + the EN reveal)

Three unrelated but small, safe UI bugs the audits found — bundled per the b64 precedent (one deploy-on-green
UI-fix pass), all value-invariant.

## 3. What this patch does

**Fix 1 — the dead §٤ short-report decomposition rows (a real display bug).** `showShortReport`'s
«من أين جاء الرقم؟» (§٤, the non-cost branch) read `v.value_decomposition.land.value` /
`building_implied.value` — **keys the engine never emits**. The engine emits `land.estimated_qar`
(`evaluate_unified.py:1708`) / `building_implied.qar` (`:1716`) — which the FULL report already reads
(`:1602/:1630`). So on a **market/income/land-led** short report the land + building rows rendered EMPTY.
Now reads the real keys (negative-safe on the building row, mirroring the full report). Live-verified on
Abu Hamour (market-led): land **١٬٧٠٠٬١٠٠** + building **٦٩٩٬٩٠٠** now render (were blank).

**Fix 2 — `run()` loading steps + error messages left in Arabic for EN users.** Since the b88 EN reveal,
the 6–20s valuation wait showed hardcoded Arabic to EN users: the 4 progress steps, the elapsed-time line,
the «جاري التقييم…» button state, the two input-validation errors, the server-error throw (all **3** eval
paths), and the catch generic-error + retry sub-line. All `t()`-wrapped with EN twins; the button restore
uses `t('ثمّن','Value it')` to match the static `data-en`.

**Fix 3 — the map modal (`openMapPicker`) — the one modal b70 missed.** The dynamically-created `.map-modal`
lacked `role="dialog"` / `aria-modal` / `aria-label` and could not be closed by keyboard. Added the three
a11y attributes + an Escape-to-close handler (the b70 pattern, with listener cleanup) + `t()`-wrapped its 3
strings (header/label/cancel). The backdrop-click-close + the three map links are preserved.

## 4. VALUE-INVARIANT

Fix 1 is a display key correction (the figures were already computed + broadcast — they were being read from
the wrong key). Fixes 2–3 are pure translation + a11y. No figure/method/rule touched; `api.py` + the engine
logic untouched (only the 2 version lines). R14: Abu Hamour amount **2,400,000** unchanged.

## 5. Verification (measured)

- Isolated `test_sprint_2_22_0b107.py` **21/21** (the real keys read + the dead keys gone + E14 the engine
  emits them · all run() strings t()-wrapped · map a11y role/aria/Escape + t() strings + links preserved) ·
  py_compile OK · `node --check` OK.
- DoD: aggregator **395/395 MATCH** · security **16/16** · surface-honesty **45/45** · broad walk **162/162
  ALL GREEN** — **1 R6/Lesson-2 re-point** (the b106 test hard-pinned its engine SLUG `rics-report-disclosures`
  which this bump changed → relaxed to a version-agnostic format check; self-caught + proactively relaxed the
  same slug-pin in the b107 test; zero assertion weakened).
- **R14 real preview 390×844** (DOM-measured, AR + EN):
  - **§٤ rows (Abu Hamour, market-led):** land «مكوّن الأرض الاسترشادي ١٬٧٠٠٬١٠٠» + building «مساهمة البناء الضمنية ٦٩٩٬٩٠٠» now RENDER (were empty); amount **٢٬٤٠٠٬٠٠٠** unchanged; no overflow.
  - **map modal:** `role=dialog` + `aria-modal=true` + `aria-label` present; **Escape closes it**; backdrop-close + links intact.
  - **EN:** the loading steps + errors + button + map strings all resolve to English; AR unchanged; **0 console errors**.
- **Personas:** lawyer APPROVE (a display key-fix revealing honestly-computed figures + pure translation +
  accessibility — no compliance impact) · linguist APPROVE (accurate EN twins; AR intact; formal register).

## 6. Deployment

- `git push origin master` FIRST, then `git subtree push --prefix "deploy v2" heroku master` (§20.112).
- **NOT yet deployed** — local build (PO: «أكمل البناء محلياً»).

## 7. Verification curl (post-deploy)

- `/api/health` → `3.1.0-sprint2.22.0b.107`.
- served `index.html`: `vd.land.estimated_qar` present · `vd.land.value` absent ·
  `m.setAttribute('role','dialog')` present · `t('نُجهّز التقرير...','Preparing the report...')` present.
- the 5-fixture villa byte-gate byte-identical to v275 (browser-UA #61).

## 8. What's NOT in this patch

- The assumptions register (built-ratio 0.77, floors-default, 50-yr depreciation) = **S3 (b108)** — next.
- The land geo-filter (b102 sibling) = **S4 (b109)**, Gate-2. The trend filter = **S5 (b110)**.

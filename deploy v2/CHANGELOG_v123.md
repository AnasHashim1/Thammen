# CHANGELOG v123 — Sprint 2.22.0b.40 «الكَيستون: حوض السوق المُعتبَر على مسار الكلفة» (DEF-UX1.2a)

**Engine:** `thammen-sprint2p22p0b40-keystone-considered` · SPRINT_TAG `2.22.0b.40` ·
api-health `3.1.0-sprint2.22.0b.40`
**Date:** 2026-06-14
**Files:** `evaluate_unified.py` (cost-led attach block + version) · `index.html` (considered render block) ·
`test_sprint_2_22_0b40.py` (new) · `docs/PHASE0_DEF_UX1.2_keystone_enrichment_recon.md` (recon)
**Class:** 🟢 ENGINE-ADDITIVE / DISPLAY-ONLY / VALUE-INVARIANT. `api.py` UNTOUCHED.
**Gate-2:** signed by delegation (the §20.70 «إثراء الكَيستون» deferral; the proposed cost-led copy was
surfaced for review and not overridden). **Gate-1:** deploy-on-green — pending the explicit «Go».

## 1. Why this matters

The keystone series surfaces the actual MoJ transactions behind the number: b38 (matched_bracket) + b39
(geo_widened) fire ONLY when the **market led**. On a **cost-led** villa (e.g. Marikh 54/541/6, the displayed
number is the DRC cost) the result screen shows **no comparables at all** — even though the engine DID
examine a market pool; it just rejected it (the geo-full pool failed its reliability bar: n=51, dispersion
0.620 > 0.30). The user is left with a cost figure and no view of the market evidence that was weighed. This
is the §20.70 deferral «the cost-led «considered-but-didn't-lead» pool (the dispersed market pool on a
cost-led villa, e.g. Marikh)».

## 2. Root cause

`evaluate_unified.py:5124` — the b38/b39 keystone attach gate fires only when `_gate['leader'] == 'market'`.
Cost-led (`_gate['rule'] == 'cost_led'`) is excluded by design (the comparables did NOT lead). The market
rows the engine examined (`geo_v2_result['primary']['transactions']` — the subject's PRIMARY-area raw
transactions, e.g. امريخ الجنوبي) are computed unconditionally (`:4281`) and live in scope at the attach
site, but were never surfaced. (Recon `docs/PHASE0_DEF_UX1.2_keystone_enrichment_recon.md`; on Marikh
`primary['comparables']` is absent — its primary method is `comparison_thin` Case 4 — so the rows are read
directly from `geo_v2_result['primary']['transactions']`.)

## 3. What this patch does

**Backend (`evaluate_unified.py`, additive — after the b38/b39 keystone block):**
```python
if _gate['rule'] == 'cost_led':
    _cc_rows = ((geo_v2_result or {}).get('primary') or {}).get('transactions')
    _cc = _keystone_comparables(_cc_rows, len(_cc_rows) if _cc_rows else 0,
                                output['valuation'].get('window_used'),
                                basis='cost_considered', pool_n=_gate.get('geo_full_n'))
    if _cc:
        _cc['dispersion'] = _gate.get('geo_full_dispersion')
        output['valuation']['considered_comparables'] = _cc
```
- Reuses the b38/b39 `_keystone_comparables` builder UNCHANGED (the `basis` value passes through; the geo
  `price_m2` ppm² fallback + newest-first sort + E12 anonymization to `{date, area_m2, total_price,
  price_per_m2}` all already handle geo rows).
- Attaches under a **NEW, distinct key `valuation.considered_comparables`** (`basis='cost_considered'`),
  never `valuation.comparables` — so the frontend renders the honest «considered» frame, never the b38
  «هي ما قرّر رقمك» overclaim.
- The «why it didn't lead» scalars ride the block: `pool_n` = `geo_full_n` (the full pool that failed),
  `dispersion` = `geo_full_dispersion`. (Both also already in `value_stack.market`.)

**Frontend (`index.html`, display-only → `how` buffer):** a new render block reading
`v.considered_comparables`, placed right after the keystone block (mutually exclusive — market vs cost_led):
header «🔍 صفقات السوق في منطقتك — اطّلعنا عليها ولم تقُد الرقم» + the why-line «الحوض الجغرافيّ فشل حدّ
الموثوقيّة (تشتّت {disp} > 0.30، n={pool_n}) — قاد التقديرَ منهجُ الكلفة (DRC)» (dir=ltr islands on the
numerics, Rule #25) + the dir=ltr `date · م² · ر.ق` table + «عرض X من N» + the CC BY 4.0 source line. A
muted left-border (`var(--muted)`, vs the bronze keystone) visually signals «considered», not «decided».
Lives in the b31 «🔍 كيف وصلنا» accordion (b34 density-open for investor/valuer).

**Out of scope (per the recon / Rule #38):** the full n=51 geo pool ROWS incl. cross-district neighbours
(those rows are discarded by `subject_geo_full_ppm2` → an engine-additive Option B, deferred); the geo
neighbour-rows enrichment on geo-led villas (b41, the §20.70 «full geo pool» sibling).

## 4. Value-invariance + privacy

- `amount/low/high/method/rule/leadership` are all written BEFORE the attach; the block only ADDS a sibling
  display key. `_keystone_comparables` returns a NEW list (no in-place mutation). Structurally value-invariant
  — mirrors the b38/b39 contract.
- E12: rows anonymized to `{date, area_m2, total_price, price_per_m2}` — no PIN/address/coordinates. CC BY 4.0.

## 5. Verification — empirical evidence

- **py_compile** OK · isolated **`test_sprint_2_22_0b40.py` 18/18** (builder `cost_considered` passthrough +
  geo key + newest-first + E12; value-invariance; engine structural [rule=='cost_led' attach, distinct key,
  market gate intact]; index.html structural [honest header, NO «هي ما قرّر رقمك», why-line, dir=ltr, in
  `how`, muted border]).
- **Siblings green WITHOUT re-point:** b38 25/25 · b39 19/19.
- **DoD:** aggregator `run_sprint_2p22p0a_suite.py` **ALL COUNTS MATCH (392)** · security **15/15** ·
  surface-honesty **45/45** · broad walk `2p22p0_pre/run_regression_2p22p0a.py` **108/108 ALL GREEN**
  (107→108, +b40; 237.4s).
- **Local E2E (live GIS, 5 anchors) ALL OK — value byte-identical to v210:** Marikh 54/541/6 → cost_led
  **2,400,000** + **considered_comparables PRESENT** (basis=cost_considered, n=29, shown=8, pool_n=51,
  dispersion=0.62, real امريخ الجنوبي rows, anonymous ✓) · أبو هامور 56/565/21 → matched **2,400,000** +
  comparables (n=37), considered absent · V001 56/647/6 → geo **3,800,000** + comparables (geo_widened n=34),
  considered absent · المعراض 55/296/13 → e25_capped **2,600,000**, neither · شقق 52/903/90 → refusal None,
  neither · **mutually-exclusive OK on all**.
- **R14 real-Chromium 390×844** (Marikh b40 payload, audience=investor): the considered panel renders in the
  OPEN «كيف وصلنا» accordion — header + the why-line «… تشتّت 0.620 > 0.30، n=51 … منهجُ الكلفة (DRC)» + 8
  dir=ltr rows (`2025-09-30 · ٥٨٩ م² · ٣٬٢٢٦٬٢٤٢ ر.ق`) + «عرض 8 من 29» + CC BY 4.0; **«هي ما قرّر رقمك»
  ABSENT anywhere** (no overclaim); headline **٢٬٤٠٠٬٠٠٠ unchanged**; **no overflow** (docScrollW 390 ==
  clientW 390, panel right-edge 355 < 390); **0 console errors/warnings**.

## 6. Deployment

```
cd /d "C:\Thammen\deploy v2"
git add evaluate_unified.py index.html test_sprint_2_22_0b40.py CHANGELOG_v123.md docs/PHASE0_DEF_UX1.2_keystone_enrichment_recon.md
git commit -m "Sprint 2.22.0b.40 (DEF-UX1.2a): cost-led «considered» comparables — surface the market pool that was examined but did not lead the cost-led number"
git subtree push --prefix "deploy v2" heroku master
git push origin master
```
(Then a separate docs-close commit: CLAUDE.md «⚡ LIVE NOW» + Session_Log §20.71 + Custom_Instructions
lean-line → b40/vN.)

## 7. Verification curl (post-deploy)

```
curl -s -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120 Safari/537.36" -X POST https://thammen.qa/api/evaluate -H "Content-Type: application/json" -d "{\"zone\":54,\"street\":541,\"building\":6}" > out.json
findstr /C:"considered_comparables" out.json
findstr /C:"cost_considered" out.json
```
Expect: amount 2,400,000 (byte-identical to v210) + `considered_comparables` PRESENT (basis cost_considered,
pool_n 51). 5-anchor value byte-gate identical to v210 (Marikh 2.4M cost-led · أبو هامور 2.4M matched ·
V001 3.8M geo · المعراض 2.6M · شقق refusal).

## 8. What's NOT in this patch (scope boundary)

- The matched_bracket (b38) + geo_widened (b39) panels — UNCHANGED.
- The geo neighbour-rows enrichment (b41, the §20.70 «full geo pool» sibling — source-area + ×adjustment
  column, the heavier bidi layout).
- The full n=51 geo pool ROWS (Option B engine-additive — deferred; the same-area subset + the disclosed
  n=51/0.620 scalars carry the story).
- Income-led / thin-without-cost-led / land / refusal surfaces — no considered panel.
- Time-normalisation of the displayed rows (deferred, as in b38/b39).
- The headline / leadership / value path — untouched (value byte-identical).

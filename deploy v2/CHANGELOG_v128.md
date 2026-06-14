# CHANGELOG v128 — Sprint 2.22.0b.45 «توحيد العلامة: لون + خطّ + إغلاق CDN»
**(brand unify — one palette, one local font, no pre-consent CDN request)**

> Engine `thammen-sprint2p22p0b45-brand-unify-tokens-font` / SPRINT_TAG `2.22.0b.45`
> / api-health `3.1.0-sprint2.22.0b.45`.
> **🟢 FRONTEND-ONLY / VALUE-INVARIANT** (CSS tokens + font-family + a `<link>` removal; `api.py`
> + the valuation engine UNTOUCHED; `evaluate_unified.py` = the 2 version lines only; the 5-anchor
> value byte-gate is identical to v218 by construction). **Files changed:** `index.html`,
> `evaluate_unified.py` (2 version lines), `test_sprint_2_22_0b25.py` (1 re-point), `CHANGELOG_v128.md`.
> **The keystone of the layout-review roadmap (Sprint B).**

## 1. Why this matters
The 4-lens layout review's top BRAND finding: the app ran **two parallel design systems** — the
app-shell (home/form/confirm/result) on **Tajawal (Google-Fonts CDN) + navy `#12344D` + bronze
`#A68252`**, and the reports on **IBM Plex Sans Arabic (local) + navy `#16324F` + bronze `#A4814A`**.
A user flowing home→form→result→report watched the brand's navy, bronze, off-white AND font visibly
shift mid-session — undercutting trust for a «trust-the-number» product. Plus the Tajawal CDN
stylesheet is a **render-blocking, pre-consent third-party request** (it fires before the consent
gate — a PDPPL point).

## 2. What this patch does (`index.html`, 3 surgical moves — recon-clean)
Recon confirmed the old brand hex lives **only** in the `:root` token defs, `'Tajawal'` is 13 CSS
`font-family` declarations + the 2 CDN lines, **0 Tajawal in the JS**, and the IBM Plex `@font-face`
is already **global** (defined for the reports, but a global family) + already served live (the
`_THMR_FONT_WHITELIST` route). So the unify is three edits, **zero new downloads, no api.py change**:
1. **Tokens → canonical (the thmr family):** `--primary` `#12344D`→`#16324F`, `--bronze`
   `#A68252`→`#A4814A`, `--bg` `#FAFAF7`→`#FBF8F2`, `--bronze-h`→`#BB955A`, `--bronze-g`→
   `rgba(164,129,74,.15)`. The legacy token NAMES are kept (aliased to the new values) → ~40 sprints
   of `var(--primary)`/`var(--bronze)` class usage keep working untouched.
2. **Font → IBM Plex Sans Arabic (already local) app-wide:** `body` + all 13 `font-family:'Tajawal'`
   → `'IBM Plex Sans Arabic'`. The app shell now matches the premium report typography. (IBM Plex
   ships 400/500/600/700; the app's `font-weight:800` maps to 700 — same as the report already does.)
3. **Dropped the Google-Fonts CDN `<link>`** (the `preconnect` + the Tajawal stylesheet) → **closes
   the pre-consent third-party request**; no Tajawal is fetched anywhere anymore.

`.thmr` (the reports) is now a layout/theme scope on the SAME tokens + font — the two systems are one.

## 3. Verification — empirical (live preview, 390×844)
- **Computed-value proof:** `body` font = `"IBM Plex Sans Arabic", sans-serif` ✓ · `--primary` =
  `#16324F` ✓ · `--bronze` = `#A4814A` ✓ · `--bg` = `#FBF8F2` ✓ · `.hbtn` bg = `rgb(164,129,74)`
  (new bronze) ✓ · `.rt` color = `rgb(22,50,79)` (new navy) ✓ · `document.fonts.check('IBM Plex…')`
  = true ✓ · **no `link[href*="googleapis"]`** (CDN gone) ✓.
- **No horizontal overflow at 390×844 on ALL screens** (home / form / confirm / result / short-report
  — `scrollW == clientW == 390`, `maxRight == 390`). IBM Plex's metrics fit the mobile target cleanly.
- **0 console errors** across the screen walk. (The screenshot tool timed out — the §20.34 capture
  hiccup; DOM measurements are the evidence channel.)
- py_compile `evaluate_unified.py` + `api.py` OK. DoD: aggregator **392 ALL COUNTS MATCH** · security
  **15/15** · surface **45/45** · broad walk **110/110 ALL GREEN**.
- **One test re-point (R6/Lesson-2):** `test_sprint_2_22_0b25.py`'s «font INSIDE .thmr only (no global
  swap)» pinned the م2-era D7 scoping (body NOT IBM Plex) that b45 **intentionally inverts** → re-pointed
  to «IBM Plex is the unified app font — .thmr + global body (b45)» (+ a stale-comment refresh). No other
  test pinned Tajawal/the CDN/the old hex (the only other match was a comment).
- Value-invariant by construction (no engine/value path touched); the 5-anchor live byte-gate re-proven
  post-deploy.

## 4. Deployment
```
git add "deploy v2/index.html" "deploy v2/evaluate_unified.py" "deploy v2/test_sprint_2_22_0b25.py" "deploy v2/CHANGELOG_v128.md"
git commit -m "Sprint 2.22.0b.45 (brand unify): one palette (navy #16324F / bronze #A4814A / paper #FBF8F2, legacy tokens aliased) + one local font (IBM Plex Sans Arabic app-wide) + drop the Tajawal Google-Fonts CDN link (closes the pre-consent request); CSS/font only, value-invariant"
git subtree push --prefix "deploy v2" heroku master
git push origin master
```
Post-deploy: `/api/health` = b45; served `index.html` carries `--primary:#16324F` + `body{…IBM Plex…}`
+ NO `googleapis`; 5-anchor value byte-gate identical to v218.

## 5. What's NOT in this patch (the roadmap)
- **The logo** stays the existing raster; the SVG/light/compact variants are with the designer (brief
  sent) — I'll wire them when they arrive. A bridge for the dark-background logo (a light chip behind it
  on the navy report header) can land separately.
- **Sprint C (the payoff):** the result-screen `thmr` hero (confident central figure + slim range bar +
  amber-not-red reservation chip), the consent-gate layering, the home trust strip — now CHEAP because the
  tokens + font are unified.
- The desktop **form-band overflow** (>~1265px) is the pre-existing fixed-580px-column quirk (mobile-first
  app) the review flagged for the desktop-layout tier — unchanged in character by b45 (the 390 target is
  clean). The honesty/uncertainty framing + value-invariance are untouched.

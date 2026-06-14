# CHANGELOG v127 — Sprint 2.22.0b.44 «تباين النصّ القانونيّ (وصوليّة AA)»
**(a11y — raise the legal/disclaimer text contrast to WCAG AA)**

> Engine `thammen-sprint2p22p0b44-a11y-contrast-legal-text` / SPRINT_TAG `2.22.0b.44`
> / api-health `3.1.0-sprint2.22.0b.44`.
> **🟢 FRONTEND-ONLY / VALUE-INVARIANT** (CSS color tokens only; `api.py` + the valuation
> engine UNTOUCHED; `evaluate_unified.py` = the 2 version-string lines only; the 5-anchor
> value byte-gate is identical to v217 by construction). **Files changed:** `index.html`
> (8 color swaps), `evaluate_unified.py` (the 2 version lines), `CHANGELOG_v127.md`.
> **First slice of the layout-review roadmap (Sprint A = asset/a11y hygiene).**

## 1. Why this matters
A brand-designer + software-engineer **layout review** (4-lens deep pass, rendered live at 390×844)
unanimously flagged the **legal/compliance text as the LEAST readable copy on the site**: the
disclaimer, the MoJ CC-BY source credit, the data-recency footer, and the Terms links all used the
decorative `--light` token (`#9CA3AF`) on the near-white background `#FAFAF7` ≈ **2.3:1 contrast** —
**below WCAG AA (4.5:1)**. The most compliance-sensitive copy («ليس تقييماً معتمداً»-class disclaimers +
the open-data attribution) was the hardest to read. This is the cheapest, highest-leverage,
zero-risk fix from the review (the top «quick win»).

## 2. What this patch does (`index.html`, surgical — 8 swaps)
The **legal/disclaimer/attribution/recency** surfaces move `--light` → `--muted` (`#6B7280`,
≈ **4.5:1** — AA pass), while the **decorative** uses of `--light` stay (offline status `.tbar-st`,
chart axis `.trend-labels`, loading timer `.lprog .lelapsed`, the number-adjacent `.cg-unit`/`.cg-mid`).
Changed surfaces:
- `.disc` (results-screen disclaimer)
- `.src-credit` + `.src-credit .en` (the MoJ CC-BY 4.0 open-data attribution, AR + EN)
- `.hfoot` (home data-recency footer «بيانات وزارة العدل حتى ديسمبر 2025»)
- `.cg-sub` (confirm-screen explanatory sub-line)
- the home Terms link + its container (inline) + the results Terms link (inline) «الشروط وإشعار الخصوصية»

No new color is introduced — both `--light` and `--muted` are existing tokens; this is a swap of
which token the legal surfaces use. No layout, no structure, no JS, no copy change.

## 3. Verification — empirical (live preview, 390×844)
- **Computed-color proof** (the authoritative channel; `preview_inspect` > screenshot for color):
  `.disc` = `rgb(107,114,128)` = `--muted` ✓ · `.src-credit` = `rgb(107,114,128)` ✓ · `.hfoot` =
  `rgb(107,114,128)` ✓ · decorative `.tbar-st` = `rgb(156,163,175)` = `--light` **unchanged** ✓
  (surgical — only the legal surfaces moved). `--light` token itself unchanged (`#9CA3AF`).
- **0 console errors** after reload + render. (The screenshot tool timed out — the known §20.34
  capture hiccup; DOM measurements are the evidence channel.)
- py_compile `evaluate_unified.py` + `api.py` OK.
- DoD: aggregator **392 ALL COUNTS MATCH** · security **15/15** · surface **45/45** · broad walk
  **110/110 ALL GREEN**.
- Value-invariant by construction (CSS color only); the 5-anchor live byte-gate re-proven post-deploy.

## 4. Deployment
```
git add "deploy v2/index.html" "deploy v2/evaluate_unified.py" "deploy v2/CHANGELOG_v127.md"
git commit -m "Sprint 2.22.0b.44 (a11y contrast): raise the legal/disclaimer/attribution/recency text from --light (~2.3:1) to --muted (~4.5:1, WCAG AA); decorative --light unchanged; CSS color only, value-invariant"
git subtree push --prefix "deploy v2" heroku master
git push origin master
```
Post-deploy: `/api/health` = b44; served `index.html` carries `.disc{…color:var(--muted)…}` etc.;
5-anchor value byte-gate identical to v217.

## 5. What's NOT in this patch (the layout-review roadmap)
- **Sprint A残り — logo:** the 727 KB raster `logo.png` recompression / SVG is **DEFERRED** — recon
  found no local image tooling (no Pillow / ImageMagick) and the logo can't be faithfully recreated as
  SVG without the source; needs an operator-supplied optimized asset (SVG ideal, or a compressed PNG).
- **The font / CDN-privacy + brand-color split → Sprint B (the keystone, unify):** Tajawal is loaded
  from the Google Fonts CDN — a render-blocking, **pre-consent third-party request** (a PDPPL point).
  Rather than self-host Tajawal (≈12 subset files + a `_THMR_FONT_WHITELIST` change, **and throwaway** if
  the font later unifies), Sprint B will **unify the app to the already-local IBM Plex Sans Arabic** +
  alias the legacy `--primary/--bronze` to the canonical `thmr` tokens — closing the CDN/privacy leak,
  unifying the two design systems, and enabling the Sprint C result-screen hero — with **zero new
  downloads**. (Recon-improved sequencing vs. the original A/B split.)
- No engine/methodology/value change; the honesty/uncertainty framing + value-invariance discipline
  are untouched.

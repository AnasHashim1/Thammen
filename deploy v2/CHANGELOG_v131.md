# CHANGELOG v131 — Sprint 2.22.0b.49 «اللوقو + كروم النموذج» (logo placement + form-field chrome)

**Engine:** `thammen-sprint2p22p0b49-logo-form-chrome` / SPRINT_TAG `2.22.0b.49` · **Date:** 2026-06-15
**Files:** `index.html` (6 surgical edits) · `evaluate_unified.py` (2 version lines) · this CHANGELOG.
**Class:** 🟢 **FRONTEND-ONLY / VALUE-INVARIANT** — `api.py` + the valuation engine UNTOUCHED; amount/low/high/method/rule byte-identical; pure CSS/markup chrome.

## 1. Why this matters
Three PO observations on the live b48 site (screenshots, gate + form): (1) the logo looks **small and ugly** on the consent gate + the working-screen top bar — «keep it on the front page, not here»; (2) a question — is the consent box necessary on every open (answered in-session: yes, it is the a24 consent gate — load-bearing for the beta, session-only, already minimized in b46; left UNTOUCHED — a compliance decision, not a UI tweak); (3) the **«رقم المبنى» field overflows the white card** (image 2).

## 2. What this patch does (all `index.html`, presentation only)
1. **Logo → home only.** Removed the gate-header logo chip (`.bgate-logo` — the `.bgate-head` keeps its navy band + title «ثمّن — تقدير سوقيّ آليّ…», which already carries the brand) and the 6 working-screen top-bar raster logos (`.tbar-logo img`). The big home-landing logo (`.hlogo`, 234px) is now the **only** `logo.png` on the site — exactly the PO's «keep it on the front page».
2. **Top-bar wordmark.** The 6 top-bar raster logos → a clean text wordmark **`<span class="tbar-wm">ثمّن</span>`** (navy `var(--primary)`, bold, IBM Plex) inside the same `.tbar-logo` click target → **keeps the click-to-home affordance**, looks intentional (not a squished raster). Mobile size 1.05rem.
3. **Form overflow fix.** `.fr3 .fg,.fr2 .fg,.fr3 input,.fr2 input{min-width:0}` — the multi-column form rows (منطقة/شارع/مبنى, and the 2-col optional rows) had grid items at the browser default `min-width:auto`, so the inputs (intrinsic ~180px) refused to shrink to their `1fr` track inside the 580px-capped card → the leftmost field overflowed the card (in RTL, out the left). `min-width:0` lets each grid item shrink to its track.

## 3. Verification — empirical evidence
- **DoD:** aggregator **395/395 MATCH** · security **15/15** · surface honesty **45/45** · broad regression walk **110/110** — **ZERO test re-points** (grep confirmed no test pins `logo.png` / `bgate-logo` / `tbar-logo` / `bgate-head` / `hlogo` / `.fr3` — pure chrome).
- **Live preview** (real flow): gate has **no logo** (navy band + title only, `headBg=rgb(22,50,79)`) · top bar = wordmark «ثمّن» navy, `onclick=go('home')` intact · home `.hlogo` kept (234px) · `logo.png` count site-wide = **1** (home only). **Overflow fixed** — measured at desktop 1280 (fields 155px, building-no left=395 ≥ card innerL=394, no overflow), at the 640px quirk width (3 cols, no overflow), and at mobile 390 (stacks to 1 col); **no horizontal doc overflow on any width**; **0 console errors**.

## 4. Deployment
```
cd /d "C:\Thammen"
git add "deploy v2/index.html" "deploy v2/evaluate_unified.py" "deploy v2/CHANGELOG_v131.md"
git commit -m "Sprint 2.22.0b.49 (logo→home-only + top-bar wordmark + .fr3 form-overflow fix)"
git subtree push --prefix "deploy v2" heroku master
git push origin master
```

## 5. Verification curl (post-deploy)
```
curl -s -A "Mozilla/5.0 … Chrome/120 Safari/537.36" https://thammen.qa/api/health   # → b49
# served index.html: logo.png count = 1 (.hlogo) ; .tbar-wm ×6 ; NO bgate-logo ; .fr3 .fg{min-width:0} ; 0 emoji
```
The **5-anchor value byte-gate must stay identical to v221** (Marikh 2.4M cost-led · V001 3.8M geo_full · المعراض 2.6M e25 · أبو هامور 2.4M matched · شقق refusal).

## 6. What's NOT in this patch (scope boundary)
- The **consent gate** (#2) is UNTOUCHED — it stays as the a24 session-only consent layer; lightening it («once per device» / inline banner) is a PO compliance decision, not done here.
- Sprint C remainder (next session, same نسق): form/confirm/refine section-label bronze chrome + segmented-control role selector · backend-emoji sweep · the logo SVG/light variant (designer track, `docs/BRIEF_logo_v1.md`).

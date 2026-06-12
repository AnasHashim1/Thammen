# CHANGELOG v108 — Sprint 2.22.0b.25 «المختصر + نظام التصميم thm-report» (م2 / Sprint B)

**Engine:** `thammen-sprint2p22p0b25-short-report-thmr` · **Date:** 2026-06-12
**Files:** `index.html` (the thm-report system + the short-report surface) · `fonts/` (IBM Plex Sans Arabic woff2 ×4 + OFL license, NEW) · `qrcode.local.js` (vendored MIT, NEW) · `evaluate_unified.py` (version strings ONLY) · `test_sprint_2_22_0b25.py` (new) · pin re-points: `test_sprint_2_22_0b15.py` + `test_sprint_2_22_0b17.py` (the D6 CTA chain) + `test_sprint_2_22_0b23.py` (the shared `_verifyUrl` gate)
**Program:** م2 of «الواجهة والتقريران» = Sprint B of the signed plan (`docs/PLAN_short_report_rollout_v1.1.md` §6-B prompt + the signed copy matrix `docs/MATRIX_short_report_copy_SIGNED.md`). 🟢 **FRONTEND-ONLY / VALUE-INVARIANT** — the engine diff is the 2 version-string lines; `api.py` UNTOUCHED; the 22-fixture byte-contract holds by construction.

## 1. Why this matters
After every evaluation the user's next step was the 10-page full report. The signed product shape is **two documents, one identity**: a 2-page **المختصر** (الزبدة + ملحق المختصين) answering «بكم؟ ولماذا؟ وماذا لو؟ وكم القسط؟» — opening FIRST (D6) — with the full report one click away. It is composed EXCLUSIVELY from the engine broadcast (`value_stack` + `leadership` + `scenarios` + `income_approach` + `value_floor` + `report_ref/fp`): **zero JS value-math** except the two declared exceptions (the D3 financing line + price-per-m²).

## 2. Root cause / what was missing
No short-report surface existed; the report CTA went straight to the b17 full report; no report design system (the reports inherited the app shell's look); the verify link existed (b23) but no scannable QR on paper; fonts/QR would have needed CDNs (rejected — local-only per the plan).

## 3. What this patch does
- **`thm-report` design system (D7-scoped):** all tokens/components namespaced under `.thmr` — navy `#16324F` · bronze `#A4814A` · paper `#FBF8F2`; **IBM Plex Sans Arabic (OFL) hosted LOCALLY** (`fonts/IBMPlexSansArabic-{Regular,Medium,SemiBold,Bold}.woff2`, official IBM plex release 1.1.0, license shipped) applied inside `.thmr` only — the app shell (Tajawal) untouched. Components: page/head/hero/range-bar/lay/card/row/scenario-table/legal/fpline/QR/buttons.
- **The short report (screens ٦/٧ of the v3 contract):** new `#shortReportScreen` + `openShortReport()`/`showShortReport(d)` from the SAME response (the b2.3 no-re-fetch pattern). **Page 1 (الزبدة):** leader-aware hero (the 4 signed labels) + the basis line + the cost↔market range bar (cost-led only) + the signed neighbor paragraph + **تفكيك المرتكز** (the DRC stack rows from `value_stack.cost` with the land detail from `value_floor`; non-cost cases fall back to the broadcast `value_decomposition`) + **الجبري ×0.90** (D2, with the b19 honesty label) + price-per-m² + **card ٣ per the matrix** (cost → the b23 `scenarios` table · market → «مدى شريحتك» on the published range · income → the NOI/cap reading from `income_approach` · land → «موقعك في نطاق المتر») + **the D3 financing line with the three assumptions EDITABLE INLINE** (20% / 25y / 4.5% defaults + «استشر بنكك») + ref/fp/**QR** + the GT hook (واتساب). **Page 2 (ملحق المختصين):** شفافية الأدلة (the dual-evidence rows per leader case, thresholds from the broadcast) + the **D-3 calibration hook** («شيت موثَّق واحد (V001 ±1%) — شيتك يدقّقها»; generic wording on land) + القراءة الدخلية التقاطعية (folded when `income_approach` is absent) + الأساس والمنهج والقيود (basis/leader/recency/MUC/2025-map) + **the VERBATIM legal block incl. IFRS 13** + QR/verify.
- **D6:** the TIER-3 CTA → `openShortReport()` («📄 التقرير المختصر / حفظ PDF»); the full report reachable via the short report's «التقرير الكامل» button (`openReport()` — the b17 screen unchanged).
- **QR (no CDN):** `qrcode.local.js` (MIT, davidshimjs, vendored with attribution) encodes the b23 verify URL; the URL builder extracted to a shared **`_verifyUrl(d)`** used by BOTH the b17 report link and the QR (one builder — no drift; the ref+fp+basis gate preserved).
- **Print:** `printing-short` A4 path — the short report prints ALONE as two pages (page-break between `.thmr-page`s), buttons/tbar hidden.
- **Refusals:** no value → an honest line + the engine's reason + the full-report escape; no scenarios/جبري/قسط.

## 4. Backend / frontend / schema
Backend: none (version strings only; `api.py` untouched). Frontend: the above. Schema: none — every binding reads EXISTING broadcast fields (verified against the real `.b20_payload_marikh.json` capture).

## 5. Verification — empirical evidence
- Isolated `test_sprint_2_22_0b25.py` **70/70** (tokens/fonts-on-disk wOF2/OFL · no-CDN for the b25 assets · screen+functions · D6 chain · the matrix verbatim pins (4 heroes + 4 neighbors + basis/evidence bindings) · the 4 constants (×0.90 · D3 editable + «استشر بنكك» · ref/fp/QR · legal+IFRS 13 · D-3 hook) · zero-fabrication (the rent-axis hint number-free; `v.amount`-math = ×0.90 only + /plot) · the D3 payment mirror (10,672 / 9,338) · the `_srCase` mirror · print rules · refusal honesty).
- Pin re-points (R6-class, behavior-preserving): b15/b17 (the CTA → short-first D6 chain) + b23 8.12 (the gate moved into `_verifyUrl`). Siblings on the final tree: b15 **49/49** · b17 **33/33** · b23 **47/47** · b24 **58/58** · b2p3 **32/32** · b3 **14/14** · b20 **69/69**.
- DoD: aggregator **392 ALL COUNTS MATCH** · security **15/15** · surface-honesty **45/45** · broad walk green (see the close-out).
- **R14 real-Chromium 390×844** with the REAL Marikh capture (+ b23-shaped scenarios/ref/fp): cost-led page renders the mockup numbers EXACTLY — hero «مرتكز التكلفة …» ٢٬٤٠٠٬٠٠٠ + the bar to 5,400,000 · تفكيك «الأرض (613 × 3,020 · n=34) = 1,851,260» + «البناء المُهلَك (BUA 479 × 2,200 × 0.5) = 526,834» · جبري 2,160,000 · قسط **≈10,672** (mockup ≈10,670) and **interactive** (30% → 9,338) · ملحق: «مطابق n=3 أقل من 10» + «جغرافي n=51 · 0.62 متنافر» + the income cross-read (12,000 بلدية / 5.2% n=46 / 2,234,724) · **QR rendered on BOTH pages from the local lib** · the other 3 variants (market/income/land) each render their signed column verbatim · fonts proven loaded from the local woff2 (`document.fonts.check` true) · print mechanics proven (the 6 `printing-short` rules live + the class toggles around a stubbed `window.print`) · **0 console errors/warnings** · docScrollW 390==390.

## 6. Deployment
```
git add <files>
git commit -m "Sprint 2.22.0b.25: short report + thm-report design system (m2/Sprint B)"
git subtree push --prefix "deploy v2" heroku master
git push origin master
```

## 7. Verification curl
```
curl -s https://thammen.qa/api/health | findstr "b25"
curl -s https://thammen.qa/ -A "Mozilla/5.0" | findstr /C:"shortReportScreen" /C:"thmr-" /C:"qrcode.local.js" /C:"IBMPlexSansArabic"
curl -s -A "Mozilla/5.0" -o NUL -w "%{http_code} %{size_download}" https://thammen.qa/fonts/IBMPlexSansArabic-Regular.woff2
```

## 8. What's NOT in this patch
- **No value change anywhere** (structural: engine diff = 2 version lines; the surface reads the broadcast).
- **The print contract PDF** «ثمن_التقرير_المختصر_v2_امريخ.pdf» was **NOT FOUND on this machine** (exhaustive search) — the match judge ran against the WEB contract (`docs/index_mockup_full_journey_v3.html` screens ٦/٧, whose report design + variant copy ARE the matrix) + Chromium print mechanics. If the PO surfaces the PDF, one look = at most a copy-tweak pass.
- **Live smoke requiring `/api/evaluate` → the deferred-smoke basket** (khazna R5 still hanging this session): the short report on the live leaders (امريخ cost-led · matched · income · land) + a live QR→/verify scan round-trip. The khazna-independent live checks (served HTML carries the b25 surfaces + the font files serve 200) run post-deploy.
- The full report v2 restructure = **م3** (its structural contract = screen ٨ of v3 + the D8 map). The first-screens identity = **م4**.
- The app-shell Tajawal CDN is pre-existing and untouched (out of D7's report scope; a shell-font decision belongs to م4 at the earliest, as its own word).

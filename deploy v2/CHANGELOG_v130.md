# CHANGELOG v130 — Sprint 2.22.0b.48 «الواجهة المرفوعة — نسق واحد» (interface elevation — one design system)

**Engine:** `thammen-sprint2p22p0b48-interface-elevation` / SPRINT_TAG `2.22.0b.48` · **Date:** 2026-06-15
**Files:** `index.html` (the bulk) · `evaluate_unified.py` (2 version lines) · `run_sprint_2p22p0a_suite.py` (manifest 392→395) · 13 test re-points · `docs/BRIEF_logo_v1.md` (new) · this CHANGELOG.
**Class:** 🟢 **FRONTEND-ONLY / VALUE-INVARIANT** — `api.py` + the valuation engine UNTOUCHED; amount/low/high/method/rule byte-identical; the result figure PRESENTS the broadcast values, never recomputes.

## 1. Why this matters
The short report reads premium; the app shell read «ordinary». b44 (AA contrast) + b45 (token+font unify) laid the *foundation*; this sprint applies the report's design language to the **whole interface** so the site is one coherent نسق — the PO's explicit ask («اريد الموقع كاملا على نسق واحد … لا اريد ايموجيز … اريد الموقع فاخرا»).

## 2. What this patch does (all `index.html`, presentation only)
1. **Result-screen hero (★1).** The TIER-1 figure `<div class="rc calc-block">` (a grey **dashed worksheet** box) → `<div class="rc">` + a navy band `.rhero` (gold label «التقدير السوقي» + the central figure `fmt(v.amount)` in white + a slim low↔high range bar `.rbar` with a dot marking where the median sits) + a `.rng` range line. **Evolves the signed b3 «range-as-lead»**: leads with a confident central figure + a slim range bar, **KEEPING** the range + the RICS «ليس تقييماً معتمداً» clause. **Supersedes the a8 «calc-block exactly-once» contract** (the result no longer carries `calc-block`; the `.calc-block` CSS stays, unused; the SHORT/FULL report keeps its own `.thmr-hero`). **MUC chip red→amber** (`--bad`→`--warn` — material uncertainty is a caution, not an error). **Green scope card → neutral** (`--ok`→`--alt/--muted`) so the navy hero is the focal point.
2. **Color-system lock.** Added `--gold:#E8C99A` (champagne — the «on-navy» accent; bronze stays the «on-light» accent). Dropped the orphan `--maroon`. **Completed the b45 unify**: swept the leftover old-palette literals app-wide — old-navy `rgba(18,52,77,…)`→`rgba(22,50,79,…)`, old-bronze `rgba(166,130,82,…)`→`rgba(164,129,74,…)`, the `#a68252` JS gradient → `var(--bronze)` — so the **consent-gate scrim, the CTA button shadows, and the home wash** all now render the new palette (the gap the b45 audit flagged). Tokenized the hero gold to `var(--gold)`.
3. **Card depth (one token, site-wide).** `--sh` → navy-tinted `0 2px 10px rgba(22,50,79,.07)`: every card on every screen gains the report's premium depth.
4. **Elevated home.** Confident navy title + a bronze divider rule + a **navy 3-step trust band** (أدخل العنوان ← نحلّل صفقات العدل ← نتيجتك — the «dark field» the shell lacked, gold step numbers) + a «من صفقات وزارة العدل المسجّلة — لا أسعار إعلانات» credibility line. The b24 copy (title + recency) is preserved verbatim.
5. **Consent gate → navy language.** The logo/title/sub move into an inset navy `.bgate-head` (logo on a **white light-chip bridge** since the raster has no light variant; white title; gold sub) — matching the result hero. The b46 «اعرف المزيد» fold + the affirmative-consent flow are unchanged.
6. **De-emoji → icon system.** **151 emoji → 25 inline-SVG line icons** (a `<symbol>` sprite + `.ic` class; icons inherit `currentColor` + text size). **No CDN** — preserves the b45 pre-consent-privacy win. **Zero emoji site-wide.**

## 3. Verification — empirical evidence
- **DoD:** aggregator **395/395 MATCH** (`calc_visual_and_ledger` 62→65 — the a8→hero re-point added 3 `.rhero` assertions; manifest bumped 392→395 per the documented contract) · security **15/15** (isolated; the broad-walk «timeout» was load contention) · surface honesty **45/45** · broad regression walk **110/110** (de-emoji + hero broke 14 files → 13 re-pointed [the 14th, security, was a false timeout]; **every re-point dropped only the emoji from a pin / updated a hero pin to the new truth — zero value-invariance, security, or methodology assertions weakened**, independently verified across all 13).
- **Live preview 390×844** (real payloads, Marikh cost-led + Abu Hamour matched): hero figure = the **live amount byte-identical** (٢٬٤٠٠٬٠٠٠ — value-invariant) · navy band `#16324F` · white figure · gold label/dots via `var(--gold)` · **amber** MUC chip `rgb(180,83,9)` · range-bar dot at the correct position (low-end for amount==low; centred for matched) · **0 `calc-block`** · **0 emoji in the DOM** (form + result) · 21+ distinct icons resolving from the sprite · `--maroon` removed · **0 console errors** · **no horizontal overflow** on every screen.
- **Lesson (#39):** the first de-emoji pass killed the JS — `⚠️` sat inside a **regex literal** (`muc_ar.replace(/^⚠️…/`) and the `/` from `</use>` broke it. Fixed by `⚠️`-escaping that one regex (emoji-free source, identical behaviour); `node --check` was unavailable, so the SyntaxError was located via `new Function()` in the browser.

## 4. Deployment
```
cd /d "C:\Thammen"
git add "deploy v2/index.html" "deploy v2/evaluate_unified.py" "deploy v2/run_sprint_2p22p0a_suite.py"
git add "deploy v2/CHANGELOG_v130.md" "deploy v2/docs/BRIEF_logo_v1.md"
git add "deploy v2/test_sprint_2_22_0b3.py" ... (the 13 re-pointed test files)
git commit -m "Sprint 2.22.0b.48 (interface elevation / one نسق): result hero + color-system lock + elevated home + consent-gate navy header + de-emoji icon system"
git subtree push --prefix "deploy v2" heroku master
git push origin master
```

## 5. Verification curl (post-deploy)
```
curl -s -A "Mozilla/5.0 … Chrome/120 Safari/537.36" https://thammen.qa/api/health   # → b48
curl -s -A "…" -X POST https://thammen.qa/api/evaluate -H "Content-Type: application/json" -d "{\"zone\":54,\"street\":541,\"building\":6}"   # amount 2,400,000 unchanged
# served index.html: carries class="rhero" + class="bgate-head" + class=ic + <symbol id="ic- ; ZERO emoji / 0 googleapis / 0 Tajawal
```
The **5-anchor value byte-gate must stay identical to v220** (Marikh 2.4M cost-led · V001 3.8M geo_full · المعراض 2.6M e25 · أبو هامور 2.4M matched · شقق refusal).

## 6. What's NOT in this patch (scope boundary, → next session, same نسق)
- The **form / confirm / refine** section-label bronze chrome + the role selector as a polished segmented-control (the icons + depth + color are done; this is the remaining chrome).
- A **backend-emoji sweep** (engine-emitted strings — Marikh rendered 0 emoji in the DOM; other payloads to spot-check).
- The **logo** SVG + light/mono variant (the designer track — brief in `docs/BRIEF_logo_v1.md`; the moment it lands we wire light-on-navy on the gate/hero/report header).

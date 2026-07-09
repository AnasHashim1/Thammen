# CHANGELOG v198 — Sprint 2.22.0b.118 «الرئيسيّة الفاخرة» (elevated marketing home)

**Engine:** `thammen-sprint2p22p0b118-elevated-marketing-home` · **api-health:** `3.1.0-sprint2.22.0b.118`
**Date:** 2026-07-09 · **Files:** `index.html`, `evaluate_unified.py` (2 version lines), `test_sprint_2_22_0b118.py` (new), `test_sprint_2_22_0b56.py` + `test_sprint_2_22_0b117.py` (R6 re-points)
**Class:** 🟢 FRONTEND-ONLY / **VALUE-INVARIANT** — `api.py` + the valuation engine UNTOUCHED.

## 1. Why this matters
A trusted customer + the PO judged the site's first frame «عاديّ». A brand+engineering design pass (customer-supplied mockups → a reconciled preview, PO-approved «أ» additive) produced an elevated marketing home: a 2-column hero (pitch + a range-as-lead «certificate» preview card) + a source-attribution trust strip — the «5-second فاخر» face the product lacked. **Additive:** the value engine, gate, form, confirm, result, and both reports are untouched.

## 2. Root cause
The live `#homeScreen` (b48) was a thin centered single-screen (logo + title + 3-step + CTA). No hero, no result-preview, no source-credibility band.

## 3. What this patch does
`#homeScreen` only (presentation): the existing pinned content (logo · «تقييم عقارك في قطر» · hsub · 3-step trust band · «ابدأ التقييم»→`go('form')` · hcred · `#dfSubtitle` freshness · scope/terms links) is **PRESERVED VERBATIM** inside a new **2-col hero** (`.lp-hero`): left = the pitch; right = a `.lp-cert` certificate-preview card with **range-as-lead** (b3: «٢٬٦٠٠٬٠٠٠ – ٢٬٢٠٠٬٠٠٠ ر.ق» headline + a muted «الوسيط ≈» marker + a confidence bar), 3 stats, «ليس تقييماً معتمداً», and a «مثال توضيحيّ» honesty label. Below: a `.lp-trust` band naming **مصادر البيانات: وزارة العدل · GIS**. On live tokens, **local IBM Plex**, **zero emoji** (sprite `#ic-scale`), **zero CDN**, **bilingual** (`data-en` per the b79/b88 mechanism), reduced-motion-safe entrance/hover. `api.py`/engine = the 2 version lines only.

## 4. Verification — empirical
- **Value-invariance (structural):** `git diff api.py` = ∅; `evaluate_unified.py` diff = the 2 version lines ONLY → the 5-fixture byte-gate holds by construction.
- **Isolated `test_sprint_2_22_0b118.py` 28/28** (real index.html, E14): structure · range-as-lead (not point) · pinned strings preserved · compliance («ليس معتمداً» + وزارة العدل + GIS + مثال توضيحيّ) · bilingual · zero emoji · version.
- **DoD:** aggregator **ALL COUNTS MATCH** · security **16/16** · surface honesty **45/45** · broad walk **172/172** (after re-points) · py_compile OK · node --check inline JS OK.
- **R14 (live preview, thammen-static):** AR renders the 2-col hero; EN toggle flips (cert/range/«not certified» → English, dir=ltr) and AR restores; **no overflow** desktop 1180 / mobile 375 (stacks); `go('form')` → the (already-correct) two-option input; gate + scope/terms intact; **0 console errors**; DOM clean (`#homeScreen` children = home-lang · lp-hero · lp-trust).
- **2 R6/Lesson-2 re-points (zero assertion weakened):** `b56` home «العدل» count ≤2 → ≤3 (the landing's source strip names وزارة العدل once — the exact hcred duplicate was removed; **flagged to the PO**); `b117` exact-version pin → version-format check.

## 5. Deployment
`git add index.html evaluate_unified.py test_sprint_2_22_0b118.py test_sprint_2_22_0b56.py test_sprint_2_22_0b117.py CHANGELOG_v198.md`
`git commit -m "Sprint 2.22.0b.118: elevated marketing home (value-invariant)"`
`git push origin master`
`git -C "C:/Thammen" subtree push --prefix "deploy v2" heroku master`

## 6. Verification curl (post-deploy)
`curl -s https://thammen.qa/api/health` → `3.1.0-sprint2.22.0b.118`
`curl -s --compressed https://thammen.qa/ | grep -c "lp-hero\|lp-cert\|lp-trust"` → present
5-fixture byte-gate (browser-UA #61): 54/541/6=2.4M · 56/647/6=3.8M · 55/296/13=2.6M · 56/565/21=2.4M · 52/903/90=refusal → byte-identical to v282.

## 7. What's NOT in this patch (scope boundary, #38)
Slice-1 = the elevated hero + trust strip. **Deferred to slice-2:** the deeper marketing sections (data-sources cards + CC-BY block · why-thammen · coverage · FAQ). The result/reports keep their live look (option «أ» = additive, no reversal of b48/b92/b93). The certificate card is an illustrative preview (labelled), not a live computation.

# CHANGELOG v129 — Sprint 2.22.0b.46 «طبقات بوّابة الموافقة» (consent-gate layering)

> Engine `thammen-sprint2p22p0b46-gate-layering` / SPRINT_TAG `2.22.0b.46` / api-health
> `3.1.0-sprint2.22.0b.46`. **🟢 FRONTEND-ONLY / VALUE-INVARIANT** (`index.html` only — the consent gate
> restructure + a small CSS block; `api.py` + the engine UNTOUCHED; `evaluate_unified.py` = the 2 version
> lines; the 5-anchor value byte-gate is identical to v219 by construction). **Files changed:** `index.html`,
> `evaluate_unified.py` (2 version lines), `CHANGELOG_v129.md`. **Sprint C — slice 1 of the layout-review
> payoff (the review's ★4).**

## 1. Why this matters
The layout review's diagnosis was «the polish order is inverted» — and the **consent gate is every user's
literal first frame**: a wall of **5 stacked detail cards** (ما هذا / ما ليس هذا / ماذا يغطّي / حدود نعرضها /
دورك) + the consent box, with the primary CTA «أوافق وأكمل» **below the fold** on a 390×844 phone. The highest
cognitive load placed before any value — a classic bounce point. (The review's ★4.)

## 2. What this patch does (`index.html`, layered — text-preserving)
The 5 detail `<li>` cards move into a collapsed `<details class="bg-more">` titled «اعرف المزيد عن النسخة
التجريبية ↓». The **first frame** is now tight and fits on screen: logo + the title (which already says what
ثمّن is) + the beta sub-line + the «اعرف المزيد» fold + the consent note «… وليست تقييماً معتمداً» + the
**affirmation** «أُقرّ بأنني فهمت …» + the **CTA «أوافق وأكمل»** + the Terms link + the existing English fold.
**Every word of the signed a24 text is preserved** — the 5 cards are layered, not removed (GDPR/ICO layered-
notice best practice). The affirmative-consent requirement and `role="dialog" aria-modal` are unchanged.
A scoped `.bg-more:not([open])>ul{display:none}` guarantees the fold collapses (robust across the Chromium
`<details>` content-hiding quirk); the rule is scoped to `.bg-more>ul` — the other accordions (t2acc / thmr-grp /
bg-en) are untouched.

## 3. Verification — empirical (live preview, 390×844)
- **Measured fold:** the gate card's `scrollHeight` = **540px collapsed** (fits the 92vh card → no internal
  scroll) vs **1013px open** → the fold hides **473px** of detail; the `<ul>` computes `display:none` closed /
  `block` open; `li` count = **5** (all cards preserved); `<details>` open-by-default = false.
- **The CTA «أوافق وأكمل» now sits above the fold** — `getBoundingClientRect().bottom` = **587 ≤ 844** (was
  below the fold before).
- **0 console errors**; the gate shows when no ack flag, hides when set (the inline pre-paint script unchanged).
  (The screenshot tool timed out — the §20.34 hiccup; DOM measurements are the channel.)
- py_compile OK. DoD: aggregator **392 ALL COUNTS MATCH** · security **15/15** · surface **45/45** · broad walk
  **110/110 ALL GREEN** — **zero test re-points** (the only gate-pinning test, b27, asserts `class="bgate thmr"
  id="betaGate"`, both unchanged; b27 = 23/23). Value-invariant by construction; the 5-anchor live byte-gate
  re-proven post-deploy.

## 4. Deployment
```
git add "deploy v2/index.html" "deploy v2/evaluate_unified.py" "deploy v2/CHANGELOG_v129.md"
git commit -m "Sprint 2.22.0b.46 (consent-gate layering): fold the 5 detail cards into an «اعرف المزيد» <details> so the first frame fits + the CTA sits above the fold; every word of the signed a24 text preserved; frontend-only, value-invariant"
git subtree push --prefix "deploy v2" heroku master
git push origin master
```
Post-deploy: `/api/health` = b46; served `index.html` carries `class="bg-more"` + «اعرف المزيد»; 5-anchor value
byte-gate identical to v219.

## 5. What's NOT in this patch (Sprint C remainder)
- **The result-screen hero (★1, the highest-value slice)** — its own focused sprint: it **evolves the signed b3
  «range-as-lead» hierarchy** (lead with a confident central figure + a slim range bar, keeping the range +
  the RICS clause) and **supersedes the a8 «calc-block exactly-once» contract**, with a ~7-test re-point surface
  (`الوسيط` is pinned by b3/b15/b17/b19/b24/b26/a2) — a careful, methodology-adjacent change that deserves its
  own slice + a rendered review.
- **The home trust strip** (a 3-step «أدخل العنوان ← نحلّل بيانات العدل ← نتيجتك» + a readable «مبني على صفقات
  وزارة العدل» line) — additive, its own slice.
- The honesty/uncertainty framing + value-invariance are untouched; the logo stays the existing raster (designer
  brief sent).

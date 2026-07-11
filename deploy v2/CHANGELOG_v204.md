# CHANGELOG v204 — Sprint 2.22.0b.126 «إصلاح تصادم الكشف والقيمة» (.rv reveal/value collision hotfix)

**Engine:** `thammen-sprint2p22p0b126-reveal-value-collision-hotfix` · **api-health:** `3.1.0-sprint2.22.0b.126`
**Date:** 2026-07-11 · **Files:** `index.html` (the reveal CSS scope + `_revealOnScroll` + the print rule), `evaluate_unified.py` (the 2 version lines), `test_sprint_2_22_0b126.py` (NEW), `test_sprint_2_22_0b125.py` (version pins relaxed, R6).
**Class:** 🟢 FRONTEND-ONLY / **VALUE-NEUTRAL** — CSS scope + a defensive reveal helper; `api.py` + the valuation engine UNTOUCHED (2 version lines only). The fix only makes already-present values VISIBLE — no valuation change; the 5-fixture value byte-gate is byte-identical.

---

## 1. Why this matters

**Anas reported a live bug (two iPhone screenshots):** every INFO-ROW VALUE was invisible — on the **confirm screen** («راجِع بيانات العقار») and inside the result-screen «التفاصيل الكاملة» fold. The field LABELS showed (العنوان / نوع العقار / المنطقة / …) but the VALUES beside them (54/541/6, فيلا منفردة, امريخ الجنوبي, R1, …) were blank. A property-review card with no data is useless and reads as broken.

## 2. Root cause

The redesign-v2 scroll-reveal primitive (Sprint 2.22.0b.120 / S0) was authored as a **bare `.rv{opacity:0}`** selector (revealed to `opacity:1` by `_revealOnScroll` adding `.rv-in`). But `.rv` is ALSO the long-standing **INFO-ROW VALUE class** — `ri(l,v)` renders the value into `<div class="rv">` (`index.html:4256`), styled by `.ri .rv{…color:var(--text)}` (+ `.calc-block .rv`, `.rv hl`). So the bare `.rv{opacity:0}` matched every VALUE span and hid it; the value spans never receive `.rv-in` (the observer only targets `#rOut .rs-sec.rv` sections), so they stayed `opacity:0` permanently. A **class-name collision** introduced by S0. It was latent since b120 (the result-screen values sat inside a collapsed accordion until S4b/b125 flattened them, and the confirm screen isn't heavily used) — surfaced now by S4b's always-open `secFull` fold + Anas testing the confirm screen.

## 3. What this patch does

- **(A) Scope the reveal primitive** (`index.html`, the `@media(prefers-reduced-motion:no-preference)` block): `.rv{opacity:0}` → **`.rs-sec.rv{opacity:0}`** and `.rv.rv-in{opacity:1}` → **`.rs-sec.rv.rv-in{opacity:1}`**. The ONLY reveal target is `.rs-sec.rv` (the single `_revealOnScroll('#rOut .rs-sec.rv')` caller), so scoping is exact — the info-row VALUE spans (`.ri .rv` / `.calc-block .rv` / `.rv hl`) are **never hidden**, and the section reveal is unchanged. The S4b print rule scoped to `.rs-sec.rv` too.
- **(B) Make `_revealOnScroll` defensive** (never leave content permanently hidden if the observer never fires — some in-app browsers, non-window scroll containers, or a throttled tab): reveal any element **already in view** immediately (`getBoundingClientRect`), observe the rest for the scroll-reveal fade, and add a **safety net** (`setTimeout` 1600ms) that reveals any element still without `.rv-in`. Content visibility is never gated solely on the IntersectionObserver. The observer + the scroll-reveal UX are preserved for the normal case.

## 4. Verification — empirical evidence

- **Isolated:** `test_sprint_2_22_0b126.py` **16/16** (reveal scoped to `.rs-sec.rv`; the bare `.rv{opacity:0}` collision GONE; the `.ri .rv` / `.calc-block .rv` VALUE styling intact; `_revealOnScroll` still targets `#rOut .rs-sec.rv`; the in-view-immediate + safety-net defensive branches present; value-neutral; version). Sibling `test_sprint_2_22_0b125.py` **63/63** (2 exact-version pins relaxed to format checks, R6/Lesson-2).
- **DoD:** aggregator **395/395 (MATCH)** · security **16/16** · surface **45/45** · **broad walk ALL GREEN** · py_compile OK · node --check (3 inline scripts) OK.
- **R14 real-Chromium 390×844 (served static, live marikh payload) — DECISIVE:**
  - **Confirm screen:** all info rows now show BOTH label AND value at **opacity 1** — العنوان → 54/541/6 · نوع العقار → فيلا منفردة · المنطقة → امريخ الجنوبي · المنطقة التنظيمية → R1 · مساحة القسيمة → ٦١٣ م² · الرقم المساحي → 54360025 · مساحة البناء الأرضي → ≈ ٣١١ م² ⓘ. `any_hidden:false`; 0 console.
  - **Result screen «التفاصيل الكاملة» fold:** 8 info rows, all values at **opacity 1** (العنوان 54/541/6 · المنطقة امريخ الجنوبي · مساحة الأرض ٦١٣ م² · نوع العقار فيلا منفردة …); `any_hidden:false`; the hero unaffected (opacity 1); 0 console; no overflow (docScrollW 390 == clientW 390).
  - **Section reveal proven working:** the `.rs-sec.rv` sections all receive `.rv-in` (in-view + observer + safety net); with the CSS transition disabled the section opacity jumps to **1** (the `.rs-sec.rv.rv-in` rule wins) — the residual `opacity:0` in the headless snapshot is a **frozen-transition artifact** (an inactive preview tab has no compositor frames to advance the 0.7s fade); in a real foreground browser the transition runs → sections visible (confirmed by Anas's live screenshot showing the sections rendered).

## 5. Deployment

```
git add index.html evaluate_unified.py CHANGELOG_v204.md test_sprint_2_22_0b126.py test_sprint_2_22_0b125.py docs/Session_Log.md
git commit -m "Sprint 2.22.0b.126: hotfix — .rv reveal/value class collision (info-row values invisible)"
git push origin master
git -C "C:/Thammen" subtree push --prefix "deploy v2" heroku master
```

## 6. Verification curl (post-deploy)

```
curl -s -A "Mozilla/5.0" https://thammen.qa/api/health | grep -o '"version":"[^"]*"'   # → 3.1.0-sprint2.22.0b.126
# 5-fixture value byte-gate unchanged: 54/541/6=2.4M · 56/647/6=3.8M · 55/296/13=2.6M · 56/565/21=2.4M · 52/903/90=null
# served / : `.rs-sec.rv{opacity:0` present, no bare `.rv{opacity:0`; getBoundingClientRect in-view reveal + the 1600ms safety net present
```

## 7. What's NOT in this patch

- The engine + `api.py` (untouched; value-neutral).
- The scroll-reveal fade-up UX (kept — this only stops the collision + adds a robustness safety net).
- A rename of the reveal class (the scope fix is sufficient and lower-risk than renaming across the codebase).

## 8. Lesson

A shared, generic class name (`.rv`) chosen for a new redesign primitive (b120) silently collided with a long-standing value class of the same name (`.ri .rv`) — hiding real content site-wide. **When adding a global reveal/animation primitive, use a namespaced class (e.g. `.reveal`/`.rvl`) or scope the selector to the intended targets, never a bare 2-letter class that may already be in use.** The R14 gate should exercise info-row VALUE visibility (not just labels/structure) on the always-visible confirm screen.

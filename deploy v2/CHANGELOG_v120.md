# CHANGELOG v120 — Sprint 2.22.0b.37 «كشف آليّة الكلفة (BUA/RCN/الاحتفاظ)» (DEF-UX9)

**Engine:** `thammen-sprint2p22p0b37-cost-mechanics-display` · **SPRINT_TAG** `2.22.0b.37` · **api/health** `3.1.0-sprint2.22.0b.37`
**Date:** 2026-06-13 · **Heroku target:** v208 (deploy-on-green)
**Files changed:** `index.html` (1 surface in `show()` — the «كيف وصلنا» accordion) · `evaluate_unified.py` (the 2 version-string lines) · `test_sprint_2_22_0b37.py` (new) · `test_sprint_2_22_0b36.py` + `test_sprint_2_22_0b31.py` (R6/Lesson-2 re-points) · `CHANGELOG_v120.md`
**Type:** 🟢 FRONTEND-ONLY / VALUE-INVARIANT (display-only; reads only already-broadcast fields) · `api.py` UNTOUCHED.

---

## 1. Why this matters

`ISSUES_LOG §4ب-2` **DEF-UX9** (المهندس · المثمّن, 🟡): «كشف BUA/RCN/معامل الاحتفاظ — إظهار الثلاثة من `value_stack.cost.*` (مبثوثة، غير معروضة)». The engineer/appraiser personas read the **result screen** and want the cost-approach (DRC) **mechanics** — how the engine got the cost number — without opening the full report. The engine has computed and **broadcast** them since b11/b18/b20 in `value_stack.cost`, but on the **result screen** only the cost *value* line showed; the **BUA × RCN × retention** breakdown was visible ONLY inside the full/short report.

## 2. Root cause (code)

`index.html` `show()` (`how` buffer — the «🔍 كيف وصلنا لهذا الرقم؟» accordion, b31): the cost note rendered ONLY the value line —
`how+='…🏗️ '+v.value_stack.cost.label_ar+': '+fmt(v.value_stack.cost.value)+' …'` — and stopped. The depreciated-building decomposition `(BUA {n} × {rcn} × {retention})` existed only in `showReport` (`:1672`) and `showShortReport` (`:1904`). So a المهندس/المثمّن staying on the result screen never saw the mechanics.

Measured-live broadcast (54/541/6, cost-led): `value_stack.cost = {value 2,378,094, land_floor 1,851,260, building_value 526,834, bua_m2 479, rcn_qar_per_m2 2,200, retention 0.5, effective_age 25, finish "ordinary", assumptions_ar "افتراضات: تشطيب ordinary · معامل احتفاظ 0.5 · عمر النظام (CGIS) أساس الاحتساب (E26)"}`. Present on **every valued villa/house** (V001 market-led carries it too: BUA 602).

## 3. What this patch does

`index.html` `show()` — the cost-value `if` block in `how` now also appends, **gated on the three fields being present** (`_vc.bua_m2 && _vc.rcn_qar_per_m2 && _vc.retention!=null` → only when the DRC actually computed them; the cost-unavailable `else if` branch is untouched):

> 🔧 آليّة الكلفة (نهج DRC): مساحة البناء BUA ≈ `<span dir="ltr">{bua_m2}</span>` م² · كلفة الإحلال {fmt(rcn_qar_per_m2)} ر.ق/م² · معامل الاحتفاظ `<span dir="ltr">{retention}</span>` ← البناء المُهلَك ≈ {fmt(building_value)} ر.ق + الأرض {fmt(land_floor)} ر.ق

+ the **broadcast** `assumptions_ar` line beneath it (no authored copy — the engine's own assumptions string). Reads the cost block once via `const _vc=v.value_stack.cost;` (DRY). The Latin/decimal tokens (`bua_m2`, `retention 0.5`) are wrapped in `dir="ltr"` islands per **Rule #25** (the `fmt()` outputs are Arabic-Indic and render RTL-naturally). **Placement = inside the «كيف وصلنا» accordion** (the appraiser-detail zone, b34 density-open for investor/valuer, one click for everyone else) → correct progressive disclosure, no clutter for the simple owner. The report/short-report rows (`:1672`/`:1904`) are UNTOUCHED (DRY siblings). Engine diff = the 2 version-string lines; **`api.py` UNTOUCHED**.

## 4. Recon-reshape

DEF-UX9 spec was directly achievable (no infeasible parts, unlike DEF-UX3 §20.67): the three fields are all broadcast. The only design call was **WHERE** — the «كيف وصلنا» accordion (not TIER-1) keeps the figure clean (the b31 «طيّ TIER-1 للمالك» discipline) while serving the appraiser via the b34 density-open default.

## 5. Verification — empirical evidence (RE-MEASURED, Rule #58, `PYTHONIOENCODING=utf-8`)

- py_compile OK.
- isolated `test_sprint_2_22_0b37.py` **22/22** (E14 — reads the REAL index.html: the gated block, the three mechanics + depreciated-building + land from broadcast fields, the broadcast `assumptions_ar`, the `dir=ltr` islands, placement in `how` not t1, the cost-value line preserved, the cost-unavailable else-branch still chains, no `v.amount/low/high` mutation, the report/short-report sibling rows untouched).
- **R6/Lesson-2 re-points:** `test_sprint_2_22_0b36.py` (the exact b36-version pin → format check) → **22/22**; `test_sprint_2_22_0b31.py` (the cost-value line's `…cost.value){how+=` literal → `🏗️ '+_vc.label_ar` + `const _vc=…` markers, because b37 moved the line into a `{const _vc=…; how+=…}` block — the «cost-value note lives in `how`, not t1» intent preserved) → **36/36**. No other test pinned the stale literal (grep-confirmed).
- DoD aggregator **392 ALL COUNTS MATCH** · security **15/15** · surface **45/45** · broad auto-walk **105/105 ALL GREEN** (104→105, +b37 test).
- **R14 real-Chromium 390×844** (served index.html + 3 LIVE-fetched payloads): **VILLA 54/541/6 [cost-led]** → the «🔧 آليّة الكلفة (نهج DRC)» line renders INSIDE the «كيف وصلنا» accordion with `BUA 479` · `كلفة الإحلال ٢٬٢٠٠` · `معامل الاحتفاظ 0.5` · `البناء المُهلَك ٥٢٦٬٨٣٤` · `الأرض ١٬٨٥١٬٢٦٠` + the assumptions line; value **٢٬٤٠٠٬٠٠٠ unchanged**; `dir=ltr` islands correct (479, 0.5 not reversed); no overflow (docSW 390). **V001 56/647/6 [market-led]** → the line present (BUA 602), value **٣٬٨٠٠٬٠٠٠ unchanged** (proves it is NOT gated on cost-led). **APT 52/903/90 [refusal]** → no cost-mechanics line, no crash. **0 console errors/warnings.**

## 6. Deployment

```
git subtree push --prefix "deploy v2" heroku master
git push origin master
```

## 7. Verification curl (post-deploy)

```
curl -s https://thammen.qa/api/health   # → 3.1.0-sprint2.22.0b.37
curl -s https://thammen.qa/ | grep -c "آليّة الكلفة"   # → served HTML carries the line
# 5-anchor value byte-gate (browser-UA POST) must stay identical to v207.
```

## 8. What's NOT in this patch (scope boundary)

- **No engine / value change.** The cost number, BUA, RCN and retention are all the engine's existing broadcast — b37 only *displays* the breakdown on the result screen. `value_stack.cost` is unchanged.
- **No new surface beyond the result-screen accordion** (the report/short-report already showed it; b37 closes the result-screen gap only).
- **No DEF-UX8** (affordability/LTV guards on the financing calculator — NET-NEW, layers on b35's UX16, needs an income input) and **no DEF-UX1** (keystone comparables — Gate-2 + recon). Both remain on the §4ب parallel track.

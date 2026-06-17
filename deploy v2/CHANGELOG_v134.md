# CHANGELOG v134 — Sprint 2.22.0b.52 «الواجهة الرشيقة: شاشة النتيجة» (result-screen lean)

> **Engine:** `thammen-sprint2p22p0b52-result-screen-lean` · **SPRINT_TAG** `2.22.0b.52`
> **Date:** 2026-06-17 · **Files:** `index.html` (the bulk — `show()`) · `evaluate_unified.py` (2 version lines) · `test_sprint_2_22_0b52.py` (new) · `test_sprint_2_22_0b15.py` + `test_sprint_2_22_0b18.py` + `test_sprint_2_22_0b31.py` (R6/Lesson-2 re-points)
> **Class:** 🟢 FRONTEND-ONLY / **VALUE-INVARIANT** — placement/fold only; `api.py` + the engine UNTOUCHED; amount/low/high/method/rule byte-identical.

## 1) Why this matters
PO directive: «DID WE REMOVE ALL THE REDUNDANT TEXT THAT MAKES THE ORDINARY USER OVERWHELMED? I NEED TO MAKE THE WEBSITE LEAN, AND THE DETAILED REPORT SHALL BE DETAILED, OTHERWISE, EVERYTHING ELSE SHOULD BE LEAN AND METHODOLOGICAL.» PO chose **«A + B: full lean»** (the safe folds **AND** folding the full MUC legal clause behind its chip — a PO-signed compliance decision).

b51 deduped/reordered the **report**. b52 leans the **result screen** (`show()`), the surface the ordinary owner actually meets first. Before b52, TIER-1 (always-visible) carried — besides the figure — the appraiser fine-print (age-sensitivity, moj sample-size, the methodology bare line) **and** the full multi-line MUC legal clause. For the simple owner that is a wall of methodology before they've absorbed the number.

## 2) Root cause
- The «كيف وصلنا» fold (b31) already collects the 9-note parade; but **age-sensitivity** (b18 §A1), **moj sample-size** (cite-n), and the **methodology bare line** were still appended to the always-visible `t1` buffer.
- The **full MUC legal clause** (`muc` buffer, built by `_mucCardHtml`) was assembled always-visible (`h=head+alerts+t1+muc+t2+t3+foot`), even though TIER-1 already carries the **MUC level chip** + «ليس تقييماً معتمداً» as the first-glance compliance signposts.

## 3) What this patch does (2 surgical, value-invariant edits in `show()`)
1. **Move the appraiser fine-print TIER-1 → the «كيف وصلنا» fold (`how`):** age-sensitivity + moj sample-size (cite-n) + the methodology bare line now build into `how` (still rendered, still disclosed, one click away) instead of always-visible `t1`.
2. **Fold the full MUC legal clause behind its chip (`_mucFold`):** `const _mucFold = muc ? _acc('… التحفّظ المادي والمعايير (RICS / IVS)', muc, false) : '';` → assembly becomes `h=head+alerts+t1+_mucFold+t2+t3+foot;`. The clause is **STILL BUILT** by `_mucCardHtml` (not deleted) — it collapses into its own labelled accordion, opened in one click.

**KEPT always-visible on TIER-1 (decision-relevant):** the figure + range-as-lead headline + the **MUC level chip** («تحفظ مادي: {level}») + the **«ليس تقييماً معتمداً»** line (a20 status appended) + the evidence one-row + the condition note. **The detailed report (`showReport`) is UNTOUCHED** — detailed stays detailed (the report still renders age-sensitivity + moj-n + methodology + the full clause).

**No compliance/honesty content removed** — the full MUC clause is folded, not deleted; the chip + «ليس معتمداً» remain the always-visible signposts; the report keeps everything.

## 4) Verification — empirical evidence
- **py_compile** (`evaluate_unified.py` + `api.py`): OK.
- **Isolated** `test_sprint_2_22_0b52.py` **17/17** (E14, reads the real index.html): age-sensitivity/moj-n/methodology → `how` (NOT t1) · MUC folds via `_mucFold` + assembly + clause-still-built · chip + «ليس معتمداً» + evidence one-row + condition note STAY t1 · the report still renders the fine-print (h+=) · value-invariance · version format.
- **DoD:** aggregator `run_sprint_2p22p0a_suite.py` **ALL COUNTS MATCH** · security **15/15** · surface-honesty **45/45** · broad walk `2p22p0_pre/run_regression_2p22p0a.py` **112/112 ALL GREEN** (101.0s; 111→112 = the new b52 test).
  - **3 R6/Lesson-2 re-points** (b52 intentionally moves age-sensitivity → fold + folds the MUC into the assembly — none weakens a value/security/methodology assertion): `test_sprint_2_22_0b18.py` #23 «age_sensitivity TIER-1» → «in the «كيف وصلنا» fold» (26/26); `test_sprint_2_22_0b31.py` «age-sensitivity STAYS t1» → «→ fold» + «valued assembly» → the b52 `_mucFold` assembly (36/36); `test_sprint_2_22_0b15.py` «valued assembly» + «MVU NOT wrapped in _acc» → «folds behind its chip via _mucFold» + honest labels on the two still-passing pins (50/50).
- **R14 (real Chromium, served index.html, 390×844):** result screen renders the lean TIER-1 (figure + range + MUC chip + «ليس تقييماً معتمداً» + evidence one-row); the full MUC clause is inside a **collapsed `<details>`** (one click); value **2,400,000** byte-identical (Marikh cost-led); **0 console errors**; **no overflow** (390==390, maxRight 370<390).

## 5) Deployment
```
cd /d "C:\Thammen\deploy v2"
git add index.html evaluate_unified.py test_sprint_2_22_0b52.py test_sprint_2_22_0b15.py test_sprint_2_22_0b18.py test_sprint_2_22_0b31.py CHANGELOG_v134.md
git commit -m "Sprint 2.22.0b.52: result-screen lean — fine-print → fold + full MUC clause folds behind its chip (value-invariant)"
git subtree push --prefix "deploy v2" heroku master
git push origin master
```

## 6) Verification curl (post-deploy)
```
curl -s https://thammen.qa/api/health        # engine = ...b52-result-screen-lean
curl -s -X POST https://thammen.qa/api/evaluate -H "Content-Type: application/json" ^
  -A "Mozilla/5.0" -d "{\"zone\":54,\"street\":541,\"building\":6}"   # 2,400,000 cost-led (byte-identical to v223/v224)
```
Live value-invariance gate (5 fixtures) must equal v224: 54/541/6 2.4M cost-led · 56/647/6 3.8M geo_full · 55/296/13 2.6M e25 · 56/565/21 2.4M matched · 52/903/90 refusal.

## 7) What's NOT in this patch
- **No deletion of compliance/honesty content** — the full MUC clause is FOLDED (still built), not removed; the chip + «ليس معتمداً» stay always-visible; CC BY / known-unknowns / the legal block are untouched.
- **No change to the detailed report** (`showReport`) — detailed stays detailed (b51 already deduped/reordered it).
- **No change to the short report** (the 2-page PDF-contract surface).
- **No value/method/leadership change** — `api.py` + the engine UNTOUCHED; the 5-fixture byte-gate is identical to v223/v224.
- The **b50 copy residuals** (the «Stage 5» leftover · «قياس دقّة» in Terms §1 · «التقييم» naming our output) — a separate copy-cleanup, not this lean pass.

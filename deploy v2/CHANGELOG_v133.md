# CHANGELOG v133 — Sprint 2.22.0b.51 «تنظيف ازدحام التقرير» (report declutter: dedup + reorder)

> **Engine:** `thammen-sprint2p22p0b51-report-declutter-dedup-reorder` · **SPRINT_TAG** `2.22.0b.51`
> **Date:** 2026-06-17 · **Files:** `index.html` (the bulk — `showReport`) · `evaluate_unified.py` (2 version lines) · `test_sprint_2_22_0b50.py` (1 R6 re-point)
> **Class:** 🟢 FRONTEND-ONLY / **VALUE-INVARIANT** — display dedup + display reorder only; `api.py` + the engine UNTOUCHED; amount/low/high/method/rule byte-identical.

## 1) Why this matters
The PO observed the report «مزدحم بالبيانات» (crowded) and asked whether it's all necessary or there's filler to cut. A recon of the live surfaces (the result screen `show()` + the full report `showReport()` + the short report) found:
- The surfaces are **already heavily decluttered** (b15 tiering · b31 fold · b32 confirm-simplify · b34 density) — so genuine *deletable* filler is **small** (good news: the product is lean).
- The full report had **one clean duplicate** (the cost value rendered 3×) + a **bad ORDER** (the reader hit ~12 fine-print appraiser notes BEFORE reaching the headline 3 values).
- The «not certified» repetition is **defensive compliance** on distinct surfaces (consent gate · forced-sale qualifier · footer · short-report pill) — **kept** (the panel's #1 trust lever).

## 2) Root cause
- **Cost-value triplicate** (`showReport`): `value_stack.cost.value` rendered at the old line 1648 (a standalone `.rn` note) + the DEF-12 three-value row + «تفكيك المرتكز». The standalone note (added in b20) became redundant when **b19** gave the DEF-12 block the canonical cost row.
- **Order**: the under-headline note-stack (condition · OSR · cost-triangulation · leadership · age-honesty · resurvey · dual-evidence/dispersion · age-sensitivity · value-floor · hbu · moj-n — ~12 `.rn` lines) rendered BEFORE the DEF-12 three-value summary, so the key numbers came last.

## 3) What this patch does (2 surgical, value-invariant edits in `showReport`)
1. **De-dup:** removed the standalone cost-value `.rn` note (+ its `unavailable_reason` else). The cost value now renders **once** — in the DEF-12 three-value block (+ «تفكيك المرتكز» on cost-led). The value + `sub_ar` + `unavailable_reason` all still render in DEF-12 → **no information lost**.
2. **Reorder:** moved the **DEF-12 three-value block** (سوقية/كلفة/جبري) UP to right after the headline range, ahead of the fine-print notes. New order: `<div class="rc">` → title → tier badge → headline range → **DEF-12 three values** → MUC clause → the fine-print evidence notes → scenarios → … The reader meets the KEY numbers first; the appraiser detail follows. `const _fs` / `_def12R` / `_ldR` all remain in scope (verified); no note references anything inside DEF-12.

**Untouched (NOT bloat — kept):** the MUC clause · «ليس تقييماً معتمداً» (footer + the specific forced-sale qualifier) · CC BY 4.0 attribution · «ما لا نعرفه» known-unknowns · the legal block · every distinct evidence/leadership/value-floor note. **No compliance/honesty content removed.**

## 4) Verification — empirical evidence
- **py_compile** (`evaluate_unified.py` + `api.py`): OK.
- **DoD:** aggregator `run_sprint_2p22p0a_suite.py` **ALL COUNTS MATCH** · security **15/15** · surface-honesty **45/45** · broad walk `2p22p0_pre/run_regression_2p22p0a.py` **111/111 ALL GREEN** (68.2s).
  - One re-point (R6/Lesson-2): `test_sprint_2_22_0b50.py` pinned the exact `b50` version strings (`ENGINE_VERSION == ...b50...` / `SPRINT_TAG == '2.22.0b.50'`) → relaxed to version-agnostic format checks (`'thammen-sprint2p22p0b' in EU` / `"'2.22.0b." in EU`); the 30 b50 **copy** checks all stayed green → b50 **32/32**. No other test pinned the moved/removed lines (b19 25/25 · b20 69/69 green WITHOUT re-point).
- **R14 (real Chromium, served index.html, 390×844) — both leader paths:**
  - **Marikh cost-led** (`.b40_marikh.json`): amount **2,400,000** / 2.4M–5.4M / cost_led → DEF-12 first row «٢٬٤٠٠٬٠٠٠ ر.ق», **DEF-12 leads before the notes** (idx 1036 < 2371/2607), cost once in DEF-12, no overflow (maxRight 370<390), **0 console errors**.
  - **V001 geo/market-led** (`.b41_v001.json`): amount **3,800,000** / 3.1M–3.8M / geo_full → DEF-12 first row «٣٬٨٠٠٬٠٠٠ ر.ق», **DEF-12 leads before «حوض المقارنات»** (idx 1025 < 2259), full render 20,137 chars.
  - `showReport` is `typeof function` after load → the reordered inline JS parsed with **no syntax break**.

## 5) Deployment
```
cd /d "C:\Thammen\deploy v2"
git add index.html evaluate_unified.py test_sprint_2_22_0b50.py CHANGELOG_v133.md docs/PERSONA_PANEL_100_b50_v223.md
git commit -m "Sprint 2.22.0b.51: report declutter — cost-value de-dup + 3-value-summary reorder (value-invariant)"
git subtree push --prefix "deploy v2" heroku master
git push origin master
```

## 6) Verification curl (post-deploy)
```
curl -s https://thammen.qa/api/health        # engine = ...b51-report-declutter-dedup-reorder
curl -s -X POST https://thammen.qa/api/evaluate -H "Content-Type: application/json" ^
  -A "Mozilla/5.0" -d "{\"zone\":54,\"street\":541,\"building\":6}"   # 2,400,000 cost-led (byte-identical to v223)
```
Live value byte-gate (5 anchors) must equal v223: 54/541/6 2.4M cost-led · 56/647/6 3.8M geo_full · 55/296/13 2.6M e25 · 56/565/21 2.4M matched · 52/903/90 refusal.

## 7) What's NOT in this patch
- **No deletion of compliance/honesty content** (MUC · «ليس معتمداً» · CC BY · known-unknowns · legal block) — defensive repetition kept by design.
- **No result-screen change** — `show()` is already well-tiered (b15/b31/b34); no safe filler to cut there without reducing disclosure prominence.
- **No short-report change** — the 2-page PDF-contract surface stays.
- **No reorder of which notes are decision-relevant vs appraiser-detail beyond moving the 3-value summary up** — the notes keep their relative order, just below DEF-12.
- The **b50 residuals** (the «Stage 5» leftover · «قياس دقّة» in Terms §1 · «التقييم» naming our output) — a separate copy-cleanup, not this bloat pass.

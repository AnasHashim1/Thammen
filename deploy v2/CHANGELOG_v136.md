# CHANGELOG v136 — Sprint 2.22.0b.55 «رشاقة التقرير الكامل» (full-report note-clustering)

> Engine `thammen-sprint2p22p0b55-report-note-clusters` · SPRINT_TAG `2.22.0b.55` · api-health
> `3.1.0-sprint2.22.0b.55`. **🟢 FRONTEND-ONLY / VALUE-INVARIANT** — `index.html` (`showReport` only)
> + 2 CSS rules; engine = the 2 version-string lines only; `api.py` + the valuation engine UNTOUCHED.
> **Files changed:** `index.html` · `evaluate_unified.py` (2 version lines) · `test_sprint_2_22_0b55.py`
> (new) · `test_sprint_2_22_0b18.py` + `test_sprint_2_22_0b52.py` (R6 re-points) · this CHANGELOG.
> Date: 2026-06-17. PO scope decision (AskUserQuestion): **«الكامل الآن، المختصر لاحقاً»** — the FULL
> report this sprint; the SHORT report deferred until the b55 mockup is re-shared.

## 1. Why this matters

The FULL report's central MV card ended with a **flat wall of ~12 fine-print notes** stacked one after
another under the DEF-12 three-value block (condition · old-stock re-anchor · cost-triangulation ·
leadership verdict · age-honesty · re-survey · dual-evidence/dispersion · age-sensitivity · value-floor ·
HBU · MoJ sample-size). For the ordinary owner that wall reads as undifferentiated noise — there is no
signpost telling them *which* notes explain the number, *which* describe their property's unknowns, and
*which* describe the data behind it. The §20.83 b55 brief calls for grouping these into **3 labeled
clusters** so the reader can navigate the appraiser detail instead of wading through it. (The reports are
already partially-leaned — b51 dedup+reorder · b52 MUC fold · b15/b31 tiering — this is the next slice the
previewed mockup specified.)

## 2. What was crowded (root)

`showReport(d)` in `index.html` — the notes block that ran from the line after the DEF-12 «الأرقام كما
يبثّها المحرك» note down to the MV card's closing `</div>`. Every note was emitted as a standalone
`h+='<div class="rn" …>'+v.X.note_ar+'</div>'` with no grouping. The other consolidation the brief mentions
(one MUC clause · one source attribution · «ليس معتمداً» once · metadata in a thin footer) was **already
satisfied** by b26/b51 (`_mucCardHtml` once, `src-credit-rep` once, the `rep-foot` thin footer already
carries engine/timestamp/fingerprint) — so the substantive b55 full-report change is the **3-cluster
grouping**.

## 3. What this patch does (frontend, value-invariant)

**`index.html` — `showReport` notes block → 3 labeled clusters** (the b31/b52 buffer-prefix-swap pattern:
every note's trigger condition + HTML string is **VERBATIM**; only the buffer prefix `h+=` →
`cNum/cProp/cData+=` changes, plus one bronze label per cluster — nothing deleted, no figure touched):

- **«حول الرقم» (`cNum`)** — how the value was derived: the leadership verdict (b20) · the old-stock
  re-anchor (b16) · the cost-triangulation note (b11) · the value-floor land-floor + implied/anchored
  decomposition (B-1).
- **«حول العقار» (`cProp`)** — what is not known about the subject: the condition-not-assessed caveat
  (a17/a19, still folds when the scenarios table answers it) · the building-age-honesty note · the
  re-survey note · the user-age sensitivity line (b18 §A1) · the HBU note (b12).
- **«حول البيانات» (`cData`)** — the evidence behind the number: the dual-evidence line (cost-led) **or**
  the bracket-dispersion line (market-led) · the registered-sales sample count (cite-n).

Emitted via a pure helper `const _repCl=(lbl,body)=>body?('<div class="rep-cl"><div class="rep-cl-h">'+lbl+
'</div>'+body+'</div>'):'';` in order number → property → data. **Empty clusters auto-omit** (a market-led
villa with no condition/age/HBU notes renders 2 clusters, not an empty «حول العقار» box). The DEF-12
three-value block still **leads** (b51 reorder preserved); the clusters follow, then the one MUC clause card.

**`index.html` — CSS:** `.rep-cl{margin-top:12px}` + `.rep-cl-h{color:var(--bronze);font-weight:700;
font-size:.74rem;margin-bottom:1px;padding-bottom:3px;border-bottom:1px solid var(--alt)}` (the unified
bronze label, b45 token) + a print rule `.rep-cl { page-break-inside: avoid; }` (alongside the existing
`.rep-def12/.rep-cover/.rep-foot` rule, which is left byte-identical per the b17 pin).

**`evaluate_unified.py`** — `ENGINE_VERSION`/`SPRINT_TAG` → b55 (the 2 lines only).

**Out of scope (kept verbatim):** the one MUC clause · the forced-sale qualifier «ليست تقييم تصفية
معتمداً» · the footer «تقييم سوقيّ آليّ وليس تقييماً معتمداً» · the MoJ source attribution + CC BY 4.0 ·
the RICS/IVS methodology note · the GT hook (`info@thammen.qa`). The SHORT report (`showShortReport`) and
the result screen `show()` are **UNTOUCHED**. `api.py` is UNTOUCHED.

## 4. Value-invariance contract

`showReport` never assigns `v.amount`/`v.low`/`v.high`; the DEF-12 rows + the ×0.90 forced-sale math are
unchanged. The displayed figures are byte-identical to b54 — only the *grouping* of the appraiser notes +
one label per cluster changed. Confirmed live on two leaders (§5).

## 5. Verification — empirical evidence

- **Isolated** `test_sprint_2_22_0b55.py` — **41/41** (the 3 clusters + helper + labels + CSS · each note's
  cluster-buffer assignment · "no note still on the old flat `h+=`" · placement after DEF-12 / before the
  MUC card · every compliance string kept · value-invariance · short-report deferred · engine-format).
- **R6/Lesson-2 re-points (test-only):** `test_sprint_2_22_0b18.py` **26/26** (test 24: report
  age-sensitivity `h+=`→`cProp+=`) · `test_sprint_2_22_0b52.py` **17/17** (test 4: report
  age-sensitivity→`cProp+=`, moj-n→`cData+=`; intent "report stays detailed" preserved).
- **DoD:** aggregator `run_sprint_2p22p0a_suite.py` **395/395 (ALL COUNTS MATCH)** · security
  `test_sprint_2p16p17_security.py` **15/15** · surface `test_sprint_2p22p0a3_surface_honesty.py` **45/45**
  · broad walk `2p22p0_pre/run_regression_2p22p0a.py` **114/114 ALL GREEN** (113→114, +b55; 117.8s).
- **R14 live Chromium 390×844** (real saved payloads, served `index.html`): **Marikh cost-led**
  (`.basket/f_marikh.json`) → **3 clusters** «حول الرقم/العقار/البيانات» + headline **٢٬٤٠٠٬٠٠٠** (2.4M,
  byte-identical) + DEF-12 leads + dual-evidence & moj-n in «حول البيانات» + every compliance string kept
  + **no overflow** (docScrollW 390 == clientW 390, maxRight 370 < 390) + **0 console errors**;
  **V001 market-led** (`.basket/f_v001.json`) → **2 clusters** (empty «حول العقار» correctly omitted) +
  the **dispersion** line (dual-evidence absent) + headline **٣٬٨٠٠٬٠٠٠** (3.8M, byte-identical) + no
  overflow + 0 console errors. Cluster header computed style = `rgb(164,129,74)` (#A4814A bronze) / weight
  700. (preview_screenshot timed out — the documented §20.34 capture hiccup; DOM measurements + inspect are
  the authoritative channel.)
- **Adversarial 4-lens verify** (parallel, independent agents that did not write the code) — **4/4 PASS,
  `weakened=false` on all:** NOTE-SET COMPLETENESS (mechanical byte-comparison of all 11 note-emitters
  HEAD↔working-tree, prefix-normalized → IDENTICAL; each once, sense-correct; the b51-removed standalone
  cost-value note not re-introduced) · COMPLIANCE SURVIVAL (no issues) · VALUE-INVARIANCE + JS INTEGRITY
  (no mutation, structure sound) · SCOPE DISCIPLINE (`api.py` ZERO diff; `showShortReport`/`show()`/
  `showConfirm` outside the diff; the 2 test edits are legitimate R6 re-points).

## 6. Deployment

```
cd /d "C:\Thammen\deploy v2"
git add index.html evaluate_unified.py CHANGELOG_v136.md test_sprint_2_22_0b55.py test_sprint_2_22_0b18.py test_sprint_2_22_0b52.py
git commit -m "Sprint 2.22.0b.55: full-report note-clustering — حول الرقم/العقار/البيانات (value-invariant)"
git subtree push --prefix "deploy v2" heroku master
git push origin master
```

> HARD GATE 1 — the Heroku push waits for Anas's explicit «go» in-session (Rule #32). `heroku auth:whoami`
> first; if unauthorized this session, hand the `git subtree push` to Anas's terminal (§20.45 lesson).

## 7. Verification curl (post-deploy, browser-UA — Rule #61)

```
curl -s https://thammen.qa/api/health | findstr /C:"2.22.0b.55"
curl -s https://thammen.qa/ | findstr /C:"rep-cl-h" /C:"حول الرقم"
```
Plus the live 5-fixture value-invariance gate (browser-UA POST): 54/541/6 2.4M cost_led · 56/647/6 3.8M
geo_full · 55/296/13 2.6M e25 · 56/565/21 2.4M matched · 52/903/90 refusal — all byte-identical to v226.

## 8. What's NOT in this patch

- **The SHORT report** (`showShortReport`) — deferred (PO option A). Its two pages are governed by the b28
  PO-delivered PDF print contract; the b55 «single بطاقة» mockup is not on disk. To be done once the mockup
  is re-shared (or a page-1 target is confirmed).
- **No deletion/consolidation of compliance repetition** — the one-MUC / one-source / «ليس معتمداً» state
  was already reached by b26/b51; the «ليس معتمداً» repetitions that remain are contextually distinct
  (global footer · forced-sale qualifier · MUC clause) and are KEPT (defensive repetition = the #1 trust
  lever, panel-confirmed §20.81; the brief says tier/consolidate, never delete).
- **No engine / value / methodology change** — `api.py` + the valuation engine untouched; value-invariant.

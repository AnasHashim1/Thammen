# CHANGELOG v109 — Sprint 2.22.0b.26 «التقرير الكامل v2» (م3 / Sprint C — the D8 surgery)

**Engine:** `thammen-sprint2p22p0b26-full-report-v2-d8` · **Date:** 2026-06-12
**Files:** `index.html` (the showReport D8 surgery) · `material_uncertainty.py` (D4 — display copy) · `evaluate_unified.py` (version strings ONLY) · `test_sprint_2_22_0b26.py` (new) · pin re-points: `test_sprint_2_22_0b17.py` (the §3 order — MUC after the number) + `test_sprint_2_22_0b19.py` (the leader-aware DEF-12 label + the de-blinded basis line) + `test_sprint_2p22p0a2_c1_geopolitical_neutralization.py` (the D4 wording — the C1 INVARIANT itself re-asserted)
**Program:** م3 of «الواجهة والتقريران» = Sprint C (the §6-C prompt + the D8 §2-C map «كما هي» + the new D4 + the PDF-audit fixes). 🟢 **PRESENTATIONAL / VALUE-INVARIANT** — engine diff = the 2 version lines; `api.py` UNTOUCHED; the D4 change is MUC display COPY (no level/decision change); the 22-fixture byte-contract holds by construction.

## 1. Why this matters
The 10-page full report contradicted itself (the «مريخ111» print = the audit subject): it called a **cost-led** number «الوسيط» twice, showed «تحفظ مادي: مرتفع» up top and «مستوى التحفظ: متوسط» below, put n=3 beside a 0.165 dispersion from a DIFFERENT pool, repeated the MUC and methodology blocks, carried an empty-ad section and an event-dated «اضطراب 28-02-2026» clause. v2 = the SHORT report's honest spine + numbered depth annexes — one voice, ~6 pages.

## 2. Root cause
`showReport` predated the b20 leadership broadcast (blind labels), rendered the MUC twice (the top card + the brief MU section whose `level` was serialized BEFORE the b20 gate raised MU), split methodology across two sites, and kept legacy prose the b23 scenarios table now answers. The MUC clause anchored on the regime's `active_since` event date.

## 3. What this patch does
- **D4 (signed):** `material_uncertainty.regime_muc` — the clause/basis drop the event-dated anchoring («({date} وما بعده)» · «قبل بدء الاضطراب الحالي بـ N يوماً») for the **banner-tied recency wording**: the clause anchors on the MoJ latest record; the basis carries the SAME days-old figure the freshness banner renders + names the banner. The C1 neutralization posture (verifiable constraint, no narrative) holds — its no-geopolitical-strings guards pass unchanged.
- **Leader-aware labels (the PDF blind-«الوسيط» fix):** the median marker + the DEF-12 first row read the b20 leadership (cost → «مرتكز التكلفة (أرض + بناء مُهلَك)» / «القيمة التقديرية (مرتكز التكلفة…)»; «الوسيط» ONLY on a true comparison median; income guarded via `income_triangulation.mode`; neutral «التقدير المركزي» otherwise). The forced-sale basis line de-blinded («القيمة التقديرية المركزية × 0.90»).
- **The MUC contradiction fix:** `renderSection`'s MU level now reads the **BROADCAST** `material_uncertainty.level` (the single truth; the brief value = fallback) — coherent on screen 4 too (ISS-A07).
- **The mixed-pool fix:** on cost leadership the pool line becomes the SIGNED dual-evidence line («شواهد السوق: مطابق n={n} (<10) · جغرافي {n}/{d} (>0.30)» — thresholds from the broadcast); on a market lead the bracket dispersion renders WITH ITS OWN n (`bracket_n_36`).
- **The D8 merges:** ONE MUC block **AFTER the number** (ص1+ص9 — the brief MU section skipped in the report loop; the refusal path keeps its clause) · ONE «المنهجية والمعايير» annex (ص2+ص9 — the a4 bare line + the brief methodology section + the a8 2025-map standards note in one card) · cost-led decomposition = **DIRECT DRC rows** from `value_stack.cost` (ص3+ص4 — no computed residual; `_decompHtml` renders only when the cost does not lead).
- **The D8 folds:** the empty-ad section folds in the report (screen 4 keeps the b14 copy) · the «حالة أفضل/أدنى» prose folds when the scenarios table answers it with numbers (the a17/a19 disclosure stays verbatim wherever no scenarios exist) · ONE DECLARED rounding line («الأرقام كما يبثّها المحرك — تدوير موحَّد من المصدر»).
- **The D8 keeps:** the SIGNED six as **NUMBERED annexes** (evidence · strata · known-unknowns · attribution · buying questions · cap-rate source — skip-safe numbering in page order) + the **thm-report identity** on the report (`repOut` joins the `.thmr` scope — the م2 fonts/tokens).

## 4. Backend / frontend / schema
Backend: `material_uncertainty.py` display strings only (D4). Frontend: the showReport surgery. Schema: none — every new binding reads EXISTING broadcast fields.

## 5. Verification — empirical evidence
- Isolated `test_sprint_2_22_0b26.py` **33/33** (D4 on the PRODUCTION `regime_muc()` incl. the banner-arithmetic identity + the C1 posture · the label decisions · the ONE-MUC order + the refusal clause · the ONE methodology annex · the DRC-direct branch · the three folds · the dual-evidence line · the broadcast MU level · the numbered six · thmr).
- `test_material_uncertainty.py` **39 OK** + C1 **7/7** (the D4 re-points carry the invariant) · DoD aggregator **392 MATCH** · security **15/15** · surface **45/45** · the full frontend sibling set green on the final tree (b15 49 · b17 33 · b19 25 · b23 47 · b24 58 · b25 74 · b14 34 · calc-visual 62 · b2p3 32 · b3 14) · broad walk → the close-out.
- **R14 real-Chromium 390×844 (the REAL Marikh capture + b23-shaped scenarios):** all 12 surgery points proven live — «مرتكز التكلفة … ≈ ٢٬٤٠٠٬٠٠٠» (no blind وسيط) · DEF-12 leader-aware · MUC ONCE, AFTER the number · the dual evidence line · the mixed-pool line gone · the condition prose folded · the DRC-direct card · the methodology annex once · the ad section folded · the rounding line · «ملحق 1…ملحق 6» · thmr — plus the market-led counter-case (الوسيط kept · `_decompHtml` renders · the condition note SHOWS with no scenarios · the pool line with its own n) and the refusal case (the MUC clause present, no DEF-12). **0 console errors/warnings**, docScrollW 390==390.

## 6. Deployment
```
git subtree push --prefix "deploy v2" heroku master
git push origin master
```

## 7. Verification curl
```
curl -s https://thammen.qa/api/health | findstr "b26"
curl -s https://thammen.qa/ -A "Mozilla/5.0" | findstr /C:"تفكيك المرتكز (أرقام DRC مباشرة)" /C:"المنهجية والمعايير" /C:"تدوير موحَّد من المصدر"
```

## 8. What's NOT in this patch
- **No value/level/decision change** — D4 is copy; the MU LEVEL was already raised by the engine; the display now agrees with it.
- **The «صفر VPS 3 / صفر IVS 105» bullet is NOT executed literally** — the same #54 adjudication as م0 (CHANGELOG_v107 §8): the report's 2025-map citations (the a8 note, primary-source triple-verified) are CORRECT and stay; the screen-٨ contract's «لا VPS 3 ولا IVS 105» line awaits the PO's explicit word against the standing a8/a22 record.
- The first-screens identity = **م4**. The full thmr re-skin of every inner report card (beyond the spine identity + annex numbering) can deepen in م4's pass if the PO wants the heavier look.
- Live evaluate smoke → the deferred basket (khazna R5).

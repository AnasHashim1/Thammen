# Sprint 2.22.0a.2 — Phase 0 Arabic Surface Audit

**Date:** 2026-05-27
**Heroku engine at audit:** `thammen-sprint2p22p0a1-qars-envelope-fallback`
**Audit cap:** 45 min (Rule #37) — completed within cap
**Method:** File-based anchor probes (Rule #34) hitting production
`https://thammen.qa/api/evaluate` → JSON capture → grep matrix

---

## 0. Executive summary

**DECISION GATE 0 verdict: PROCEED to Phase 1 (scope locked).**

All five Phase-0 STOP-criteria are clear:
- C1 geopolitical phrases CONFIRMED present in all 4 rendered anchors (4/4)
- C2 internal-doc-leak phrases CONFIRMED present in 1 of 4 anchors (default villa brief)
- Pattern B refusal cases distinguishable at engine dispatcher level
- C5 buyer prescriptive language CONFIRMED in default brief render
- Phrase volume within KICKOFF estimates (no 3× ballooning)

Two KICKOFF estimates require minor correction (noted per Rule #36):
- Pattern A: 4 user-visible sites (not 5 as KICKOFF stated); 5th was a comment block
- Pattern B: dispatcher exists; one new trigger required + 1 misroute fix
  (smaller than KICKOFF "3 new cases" framing)

Both corrections REDUCE scope vs. KICKOFF, not increase it. No re-scope.

---

## 1. Anchor inventory

Production probe (`probe_phase0_anchors.py`), 4 POSTs to `/api/evaluate`,
2026-05-27, ~25–30 min wall-clock from one Heroku-router-region client.

| Anchor          | Payload      | Status | Elapsed | asset_type        | val | refusal_trigger        | sections |
|-----------------|--------------|--------|---------|-------------------|-----|------------------------|----------|
| villa           | 56/565/21    | 200    | 24.32 s | standalone_villa  | None | (none — full brief)   | 5        |
| apartment_bldg  | 52/903/90    | 200    |  5.88 s | apartment_building | None | comp_density_sparse  | 1        |
| tower H1        | 69/255/75    | 200    |  5.78 s | apartment_building | None | comp_density_sparse  | 1        |
| refusal/unknown | 70/300/25    | 200    |  5.48 s | unknown           | None | comp_density_sparse  | 4        |

Observations (Rule #36, actual sample/window):
- **2 of 4 anchors fired the same generic refusal** (`comp_density_sparse`)
  even though their failure modes differ: 52/903/90 + 69/255/75 are
  known-asset-type / sparse-MoJ-comps, while 70/300/25 is
  **classifier-failure** (asset_type=unknown, district=null,
  plot_area_m2=null — QARS lookup yielded nothing). Pattern B target.
- **All 4 anchors carry C1 geopolitical prose** in
  `material_uncertainty.muc_clause_ar` (the MUC banner). Highest-urgency.
- Anchor 69/255/75 (Sprint 2.21.4 H1 anchor in `لوسيل 69`) returns
  `apartment_building` rather than `tower` and fires the same generic
  refusal — orthogonal classifier observation, NOT in 2.22.0a.2 scope.
  Logged for a future Sprint, not blocking.

Raw captures: `docs/phase0/brief_<slug>.json` (full JSON bodies),
`docs/phase0/brief_<slug>.strings.txt` (flat string dumps for grep).

---

## 2. Phrase mapping (Phase 0.2)

Cross-tab of ChatGPT-flagged phrases vs. rendered anchors.
`.` = not found, integer = match count.

| phrase                  | 52_903_90 | 56_565_21 | 69_255_75 | 70_300_25 | scope verdict |
|-------------------------|:---------:|:---------:|:---------:|:---------:|:--------------|
| **C1 geopolitical**     |           |           |           |           |               |
| `الحرب الإقليمية`        |    1      |    2      |    1      |    2      | CONFIRMED — fix |
| `هرمز`                  |    1      |    2      |    1      |    2      | CONFIRMED — fix |
| `نزوح سكاني`             |    1      |    2      |    1      |    2      | CONFIRMED — fix |
| `انهيار`                |    1      |    2      |    1      |    2      | CONFIRMED — fix |
| `الاقتصاد`              |    .      |    .      |    .      |    .      | NOT IN PROD — drop |
| `جيوسياسي`              |    .      |    .      |    .      |    .      | NOT IN PROD — drop |
| **C2 internal-doc leak**|           |           |           |           |               |
| `Project Instructions`  |    .      |    1      |    .      |    .      | CONFIRMED — fix |
| `Sprint 2.`             |    .      |    1      |    .      |    .      | CONFIRMED — fix |
| `Operational_Rules`     |    .      |    .      |    .      |    .      | NOT IN PROD — drop |
| `CHANGELOG`             |    .      |    .      |    .      |    .      | NOT IN PROD — drop |
| **C3 tier badge**       |           |           |           |           |               |
| `موثوق`                 |    1      |    3      |    3      |    3      | CONFIRMED — fix |
| `إرشادي`                |    .      |    2      |    4      |    .      | CONFIRMED — fix (companion) |
| `reliable` (en)         |    1      |    1      |    1      |    2      | CONFIRMED — fix |
| `indicative` (en)       |    .      |    .      |    5      |    .      | CONFIRMED — fix |
| **C4 IVS/RICS reframe** |           |           |           |           |               |
| `ليس تقييم`              |    1      |    3      |    1      |    2      | CONFIRMED — fix |
| `RICS`                  |    3      |   15      |    3      |   11      | LIVE (kept in cite) |
| `IVS`                   |    5      |   17      |    5      |   16      | LIVE (kept in cite) |
| **C5 buyer prescriptive**|          |           |           |           |               |
| `لا تدفع`                |    .      |    1      |    .      |    1      | CONFIRMED in default brief — fix |
| `ابدأ بعرض`              |    .      |    1      |    .      |    1      | CONFIRMED in default brief — fix |
| `لا تُصرّ`                |    .      |    .      |    .      |    .      | NOT IN PROD — drop |
| **Pattern A Latin-in-Ar**|          |           |           |           |               |
| `(RICS`                 |    .      |    2      |    .      |    .      | CONFIRMED — LRM target |
| `QAR` / `PIN` / `zone`  |    .      |    .      |    .      |    .      | NOT IN PROD — drop these |

### Source-code origin of each LIVE phrase

| phrase                                | origin (file:line)                                |
|---------------------------------------|---------------------------------------------------|
| `الحرب الإقليمية وإغلاق هرمز`           | market_regime.py:150 (ShockLayer.name_ar)         |
| `نزوح سكاني`                           | market_regime.py:164 (ShockLayer.name_ar)         |
| `انهيار حجم المعاملات`                  | market_regime.py:174 (ShockLayer.name_ar)         |
| `صدمات الحرب وهرمز والنزوح السكاني`     | market_regime.py:314 (regime_recommendation prose) |
| shock_summary_ar interpolation site   | material_uncertainty.py:164 (`'، '.join(...)`)    |
| muc_clause_ar formatted text          | material_uncertainty.py:171–186                   |
| `(Project Instructions §3)`           | stock_strata.py:93 (STRATUM_DESC_AR)              |
| `Sprint 2.16.0 (الإصدار الحالي):`       | stock_strata.py:445–449 (sprint_scope_caveat_ar)  |
| C4 disclaimer long-form (3 places)    | api.py:785, evaluate_v3.py:356, evaluate_property.py:474 |
| C4 disclaimer short-form (5 places)   | evaluate_unified.py:1956, 2394, 2608, 2714, 2847  |
| C4 `لا يُصدر... (RICS/IVS)` list item   | api.py:843 (`what_thammen_does_not[0]`)            |
| C5 negotiation note Anchor            | (see §3 below — separate locator)                  |

---

## 3. C5 buyer-prescriptive locator

The negotiation note (`brief.sections[0].content.note` in default villa
brief and unknown-asset refusal) reads:

> `لا تدفع أكثر من وسيط MoJ + 10%. ابدأ بعرض أقل 10% من التقييم.`

Phase 0.2 confirmed this fires in the **default brief render** (both
56/565/21 default-evaluation and 70/300/25 refusal paths). KICKOFF
condition for keeping C5 in scope is met → **C5 stays in scope.**

Origin needs Phase 1 grep (anticipated: `output_briefs.py` negotiation
section builder). One additional grep in Phase 1.

---

## 4. Pattern B — refusal-case map (Phase 0.3)

The dispatcher `_compute_refusal_reason()` (evaluate_unified.py:181–268)
already routes by a 6-trigger §5.3 precedence chain:

| Row | trigger_id                  | Condition                                                                 |
|-----|-----------------------------|---------------------------------------------------------------------------|
| 1   | density_gated_district      | district in `_DENSITY_GATED_DISTRICTS`                                    |
| 2   | spatial_ambiguity           | method == `'asset_type_reality_stop'`                                     |
| 3   | asset_scale_extreme         | asset_type == `'compound_large'` AND plot_area_m2 ≥ 15_000                |
| 4   | asset_class_out_of_scope    | method == `'out_of_scope_v1'`                                             |
| 5   | regime_shift                | district matched in registry (empty in 2.22.0a — always inert)            |
| 6   | comp_density_sparse         | DEFAULT FALLBACK                                                          |

KICKOFF's "3 cases" requested:
- **data_missing** → `comp_density_sparse` (existing, OK)
- **classifier_failure** → NEW trigger (when QARS lookup failed → asset_type='unknown')
- **coverage_gap** → `density_gated_district` (existing, OK)

### The bug Pattern B must fix

Anchor 70/300/25 fires `comp_density_sparse` ("less than 5 comparable
transactions") when reality is: **QARS legacy snapshot has 0 features
for this PIN — the engine doesn't even know what type of property it is**.
The user reads "I need more transactions" when they should read
"the address itself wasn't found".

The dispatcher falls through rows 1–5 (district=null, method='insufficient_data'
not 'asset_type_reality_stop', asset_type='unknown' not 'compound_large',
no regime event match) and lands on row 6 (default).

### Pattern B Phase 1 plan

1. Add 7th trigger `classifier_failure` to `refusal_templates.py` with
   neutral Arabic copy ("لم نتمكّن من تحديد نوع العقار من البيانات
   الحكومية المتاحة — يُحتمل أن يكون العنوان غير مفهرس أو خارج التغطية
   الحالية") + English mirror.
2. Insert one new row in dispatcher precedence chain (between current
   rows 1 and 2, i.e. row 2 becomes 3 etc.):
   ```python
   # 2. classifier_failure — engine could not classify (QARS coverage gap)
   if asset_type == 'unknown' and method != 'asset_type_reality_stop':
       return get_refusal_template('classifier_failure', **base_ctx)
   ```
   This pre-empts row 3 (spatial_ambiguity stays exclusive to the
   reality-check stop path) and row 6 (comp_density_sparse stays
   exclusive to known-asset-type sparse-MoJ cases).
3. Multi-AI validation on the new Arabic copy (Rule #54).

KICKOFF F5 footer note ("5 active triggers" → "6 active in /5" → "7 active
in /a2") to be amended in CHANGELOG.

---

## 5. Pattern A — LRM bidi sites (Phase 0.2 cross-check)

KICKOFF named 5 sites; **exactly 4 user-visible Arabic-with-Latin
strings need LRM wrapping**. The 5th KICKOFF line number pointed at a
comment block (output_briefs.py:579/580/916 are comments; the adjacent
Arabic title lines are 583/921, and 921's `title_ar` is purely Arabic
with no Latin tokens — does NOT need LRM).

Locked Pattern A sites:

| # | File                    | Line(s)   | String head                                        |
|---|-------------------------|-----------|----------------------------------------------------|
| 1 | material_uncertainty.py | 172–175   | `⚠️ تحفظ مادي وفق RICS Red Book Global Standards…` |
| 2 | material_uncertainty.py | 369–373   | `للتوافق مع معايير RICS Red Book Global Standards…` |
| 3 | output_briefs.py        | 583       | `'تحفظات مادية وفق RICS Red Book Global Standards…'` |
| 4 | index.html              | 737       | `'⚠️ تحفظ مادي وفق RICS Red Book Global Standards…'` |

Pattern: each Arabic sentence contains Latin/digit tokens that may
visually reverse under `dir="rtl"` rendering (Operational_Rules #25).
Wrap each Latin/digit run with U+200E LRM markers.

---

## 6. Locked Phase 1 scope (post-Gate-0)

### Commit order (per KICKOFF §5)

1. **C1** — neutralize geopolitical prose in `material_uncertainty.regime_muc()`
   - Replace `shock_summary_ar` join (line 164) with neutral VPGA 10 phrase
   - Replace `shock_summary_en` join (line 165) with English mirror
   - Touch `market_regime.py:314` (`'البيانات لا تعكس صدمات الحرب…'` prose
     in `regime_recommendation` lag warning) — this is a separate prose site
     not currently surfaced via the rendered API path, but emit could change
     in a future Sprint. Defensive scope-include with neutral phrasing.
   - Leave `market_regime.py:150/164/174` ShockLayer.name_ar fields IN PLACE
     (data model untouched; only the rendering layer changes — preserves the
     internal audit trail of why ceiling math drops, without exposing the
     geopolitical narration to users).
   - Multi-AI validation required (Rule #54).

2. **C2** — remove internal-doc leaks
   - stock_strata.py:93 — delete `(Project Instructions §3)` reference
     (mechanical: replace with empty parens removal or "وفق منهجية ثمّن")
   - stock_strata.py:445–449 — replace `sprint_scope_caveat_ar` body with
     version-agnostic phrasing OR remove the field. Decision: rewrite to
     "هذه الطبقات مقدّمة كشفافية إضافية — القيمة الرئيسية أعلاه لم تتأثّر."
     (Mechanical, no multi-AI needed — purge.)

3. **A** — LRM bidi wrap at 4 sites (table §5)
   - Mechanical fix. Wrap each Latin/digit run with `‎…‎`.

4. **C3** — relabel `موثوق` tier badge
   - Multi-AI validation required (semantic substitution).
   - Anticipated replacement: `موثوق` → `تغطية بيانات جيدة` (or similar
     coverage/sample-quality language); `إرشادي` likely stays.
   - Need full inventory grep in Phase 1.

5. **C4** — reframe `ليس تقييماً عقارياً معتمداً وفق RICS/IVS`
   - 8 sites to touch (3 long-form + 5 short-form) + 1 list item in api.py:843
   - Replace with: `ولا يُعتبر تقرير تثمين رسمي صادر عن مثمّن مرخّص وفق
     معايير RICS/IVS` (per KICKOFF directive)
   - Multi-AI validation required.

6. **C5** — reframe buyer prescriptive negotiation note
   - Multi-AI validation required.
   - Phase 1 step 1: grep to find the construction site (anticipated:
     output_briefs.py).
   - Anticipated reframe: imperative → descriptive market-liquidity
     reading ("…المشترون عادةً لا يدفعون فوق وسيط MoJ بأكثر من 10%؛
     عروض البداية في السوق الحالي تميل إلى…").

7. **B** — refusal CTA differentiation
   - Add `classifier_failure` template to refusal_templates.py (7th trigger).
   - Add dispatcher row 2 in `_compute_refusal_reason()` (asset_type='unknown'
     not via reality_stop → classifier_failure).
   - Multi-AI validation on new Arabic copy.
   - **Largest regression surface — ship last per KICKOFF order.**

### Out of scope (deferred, NOT addressed in 2.22.0a.2)

- Anchor 69/255/75 returning `apartment_building` rather than `tower`
  (classifier observation, orthogonal — could be Sprint 2.21.4 followup).
- Cosmetic UX from Session_Log §15.5: hide negotiation box when val=None
  (2.21.0.12 candidate, separate Sprint).
- shock_layer name_ar fields in `market_regime.py` data model (kept).
- Adjustments-math change in `market_regime.py` calibration constants
  (ceiling-multiplier values unchanged — only the *prose explaining them*
  is reframed).

### Estimated edit footprint

| Pattern | Files touched | Approx lines |
|---------|--------------|--------------|
| C1      | material_uncertainty.py (+ market_regime.py:314 defensive) | ~15 |
| C2      | stock_strata.py | ~8 |
| A       | material_uncertainty.py, output_briefs.py, index.html | ~12 (LRM-wrap insertions) |
| C3      | TBD per Phase 1 grep (estimate: 4–6 files) | ~20–30 |
| C4      | api.py, evaluate_unified.py (×5), evaluate_v3.py, evaluate_property.py | ~10 |
| C5      | output_briefs.py (most likely) | ~6 |
| B       | refusal_templates.py, evaluate_unified.py | ~25 |
| **Total** | 7–9 files | ~95–110 lines |

Within KICKOFF estimates — proceed.

---

## 7. Gate 0 decision

**Verdict: PROCEED to Phase 1.**

- Urgent-tier C1 phrases found in production: 4/4 anchors ✓
- Urgent-tier C2 phrases found in production: 1/4 anchors (default villa) ✓
- Pattern B distinguishable: yes — dispatcher exists, +1 trigger needed ✓
- C5 in default render: yes ✓
- Phrase volume reasonable, no 3× ballooning ✓

Scope is locked per §6 above. No STOP report needed.

---

*Authored by Claude Code 2026-05-27 in Sprint 2.22.0a.2 Phase 0. All
findings reproducible via probes preserved in `docs/phase0/` (raw JSON +
flat strings dumps) and `probe_phase0_anchors.py` + `probe_phase0_summarize.py`
+ `probe_phase0_phrase_grep.py` (throwaway file-based probes per Rule #34,
to be cleaned up in Sprint closeout per Operational_Rules #41 pending).*

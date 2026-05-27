# Sprint 2.22.0a.2 — Consolidated Multi-AI Validation Batch

**Sprint:** 2.22.0a.2 (Arabic copy correctness + refusal CTA differentiation)
**Validators required:** GPT-5 + Gemini (Rule #54 — two-approval consensus)
**Audit anchor:** [docs/PHASE0_ARABIC_SURFACE_AUDIT.md](PHASE0_ARABIC_SURFACE_AUDIT.md)
**Author:** Claude Code, 2026-05-27
**Status:** PENDING external validation runs by Anas

---

## How to use this packet

1. For each of the 7 items below (C1, C2-replacement, C3, C4, C5, B, + B2/B3-architecture-confirmation), copy the **prompt block** verbatim into both GPT-5 and Gemini.
2. Paste both responses back under the item's `## Validator responses` placeholder.
3. **Two approvals (both AI flag-free) required** for the proposed replacement to be committed. Any flag → revise, re-validate.
4. The B2/B3 architecture confirmation (§7) is a decision question for Anas, NOT a multi-AI item — read my analysis and either accept or override before B implementation.

Rule #54 lockstep order (KICKOFF §5): C1 → (C2 mechanical already shipped in commit 2) → A (already shipped) → C3 → C4 → C5 → B. Each pattern commits independently as its two-AI approvals land.

---

## §1. C1 — Geopolitical narration → neutral VPGA 10 framing

### Original text (verbatim from production, anchor `material_uncertainty.muc_clause_ar` and English mirror)

**Arabic** (built at `material_uncertainty.py:164`, `:178` — `regime_muc()` function):
> اضطراباً جوهرياً نشطاً: تصحيح ما بعد المونديال، الحرب الإقليمية وإغلاق هرمز، نزوح سكاني، انهيار حجم المعاملات.

**English** (built at `material_uncertainty.py:165`, `:196`):
> material disruption at the valuation date (2026-02-28 onwards): post-World-Cup correction, regional war and Hormuz Strait closure, population outflow, transaction-volume collapse.

**Companion site** (`market_regime.py:314`, the regime_recommendation lag-warning prose — *not* surfaced through current rendered API path but defensive scope-include):
> البيانات لا تعكس صدمات الحرب وهرمز والنزوح السكاني

### Proposed replacement

**Arabic** (replaces the `shock_summary_ar` join + its interpolation in `muc_clause_ar`):
> قيوداً جوهرية على شواهد السوق المتاحة، في ظل فجوة طويلة في تحديث بيانات وزارة العدل وضعف في حجم المعاملات الحديثة المنشورة.

**English** (replaces `shock_summary_en` join + interpolation in `muc_clause_en`):
> material constraints on available market evidence, given an extended gap in the publication of Ministry of Justice transaction data and a low volume of recently published transactions.

**Companion site replacement** (`market_regime.py:314`):
> البيانات الأساسية لا تعكس تطوّرات السوق منذ آخر تحديث منشور.

### Rationale

- **Regulatory standard satisfied:** RICS Red Book Global Standards (effective 31 January 2025) — **VPGA 10 §6** (Material Valuation Uncertainty: cause of uncertainty MUST be identified, but identification does not require attribution to political events). The replacement cites the verifiable, RICS-aligned cause: **constrained current market evidence + data-freshness gap**.
- **What the replacement does NOT claim:**
  - No attribution to specific geopolitical events (war, Hormuz closure, population displacement, transaction collapse).
  - No causal narrative tying market behaviour to military or political actors.
  - No quantitative claims about population, LNG capacity, or shipping volumes (avoiding macro narration outside our verifiable scope).
- **What it preserves:**
  - The MVU clause's regulatory framing (VPGA 10 + VPS 6 + IVS 106).
  - The honest acknowledgement that current market evidence is constrained.
  - The downstream calibration math in `market_regime.py` (buyer ceiling × 1.00 etc.) — those numerical adjustments stay intact; only the prose explaining them is reframed.
- **Internal-only data preserved:** `market_regime.py:150/164/174` ShockLayer `name_ar` fields are NOT removed (data model untouched). They retain the internal audit trail of why the calibration was set; they're simply not interpolated into user-visible copy any more.

### Prompt to validators (paste verbatim)

```
Review this Arabic text for a Qatar real-estate Automated Valuation Model (AVM)
platform. The text is a Material Valuation Uncertainty (MVU) disclosure that
appears in every valuation report when market conditions are constrained. The
platform is published in Qatar; the author is a Qatari company building under
RICS Red Book Global Standards (effective 31 January 2025) — VPGA 10 (Material
Valuation Uncertainty) — and IVS (effective 31 January 2025) — IVS 106
(Documentation and Reporting).

ORIGINAL TEXT (currently in production):
"اضطراباً جوهرياً نشطاً: تصحيح ما بعد المونديال، الحرب الإقليمية وإغلاق هرمز،
نزوح سكاني، انهيار حجم المعاملات."

PROPOSED REPLACEMENT:
"قيوداً جوهرية على شواهد السوق المتاحة، في ظل فجوة طويلة في تحديث بيانات
وزارة العدل وضعف في حجم المعاملات الحديثة المنشورة."

ENGLISH MIRROR — ORIGINAL:
"material disruption at the valuation date (2026-02-28 onwards): post-World-Cup
correction, regional war and Hormuz Strait closure, population outflow,
transaction-volume collapse."

ENGLISH MIRROR — PROPOSED:
"material constraints on available market evidence, given an extended gap in
the publication of Ministry of Justice transaction data and a low volume of
recently published transactions."

Please assess:
(a) Any regulatory/legal exposure (RICS / IVS / Qatari real-estate disclosure
    norms / political-speech concerns in the local context).
(b) Any factual claim that overstates authority or makes a claim the platform
    cannot defend with its own data.
(c) Any phrasing that could be misread by a non-expert Arabic reader (clarity,
    Modern Standard Arabic register, RTL readability).
(d) Whether the replacement adequately fulfils VPGA 10's §6 requirement to
    identify the CAUSE of uncertainty — without attributing it to specific
    political events that the platform cannot independently verify.

Output one of:
  APPROVED — replacement is suitable, no changes needed
  FLAGGED — list specific concerns and (if possible) a counter-proposal
  REVISE — suggest a different replacement text

Be specific. This is a regulatory-disclosure surface, so erring on the
conservative side is preferred.
```

### Validator responses

**GPT-5:** _(paste here)_

**Gemini:** _(paste here)_

**Decision:** _(2 approvals → commit; any flag → revise)_

---

## §2. C2 — `sprint_scope_caveat_ar` replacement (the non-mechanical part)

### Original text (verbatim, `stock_strata.py:445–449`)

> Sprint 2.16.0 (الإصدار الحالي): الـ stratification شفافية فقط — القيمة الرئيسية في الأعلى لم تتغير. اختيار الـ stratum المناسب لفيلتك حسب العمر والتشطيب يبقى قراراً للمستخدم. الإصدارات القادمة قد تتيح اختيار stratum مباشرة.

### Proposed replacement

> هذه الطبقات مقدّمة كشفافية إضافية — القيمة الرئيسية أعلاه لم تتأثّر. اختيار الفئة المناسبة لعقارك حسب العمر والتشطيب يبقى قرار المستخدم.

### Rationale

- **What's removed:**
  - `Sprint 2.16.0 (الإصدار الحالي)` — internal-doc / version self-reference (KICKOFF C2 target).
  - `الإصدارات القادمة قد تتيح اختيار stratum مباشرة` — roadmap promise that risks setting an expectation we may not deliver.
  - The English/Arabic code-switching of `الـ stratification`, `الـ stratum` — replaced with native Arabic terms (`الطبقات`, `الفئة`).
- **What's preserved:**
  - The honest disclosure that stratification is *informational* (not value-changing).
  - The user-decision framing.
- **What it does NOT claim:**
  - No version self-reference; no roadmap promise; no English technical jargon mixed into user copy.

### Prompt to validators

```
Review this Arabic text for a Qatar real-estate AVM. It appears in the stock-
stratification panel of villa valuation reports as a transparency disclaimer.

ORIGINAL TEXT:
"Sprint 2.16.0 (الإصدار الحالي): الـ stratification شفافية فقط — القيمة الرئيسية
في الأعلى لم تتغير. اختيار الـ stratum المناسب لفيلتك حسب العمر والتشطيب يبقى
قراراً للمستخدم. الإصدارات القادمة قد تتيح اختيار stratum مباشرة."

PROPOSED REPLACEMENT:
"هذه الطبقات مقدّمة كشفافية إضافية — القيمة الرئيسية أعلاه لم تتأثّر. اختيار
الفئة المناسبة لعقارك حسب العمر والتشطيب يبقى قرار المستخدم."

Please assess:
(a) Does the replacement remove the internal-doc references (sprint version,
    English technical jargon) without losing the substantive disclosure?
(b) Any regulatory/legal exposure in either version.
(c) Modern Standard Arabic register suitable for a professional valuation
    platform; clarity for a non-expert reader.
(d) Any concerns about removing the "future versions may allow direct stratum
    selection" forward-looking statement.

APPROVED / FLAGGED / REVISE — be specific.
```

### Validator responses

**GPT-5:** _(paste here)_

**Gemini:** _(paste here)_

**Decision:** _(2 approvals → commit)_

---

## §3. C3 — `موثوق` tier badge relabel

### Inventory (Phase 0 grep — to be expanded in Phase 1 step 4)

Phase 0 found `موثوق` in all 4 anchors (52_903_90:1, 56_565_21:3, 69_255_75:3, 70_300_25:3). The label is set at multiple sites; full Phase 1 grep pending — preliminary list:
- `tier_label` rendering in `output_briefs.py`
- `confidence` field labels across the engine
- companion `إرشادي` (indicative) appears 2× and 4× in 56/565/21 and 69/255/75

### Original tier vocabulary

| Code | Arabic label (current) | English (current) |
|---|---|---|
| reliable    | موثوق    | reliable    |
| indicative  | إرشادي  | indicative  |
| fallback    | احتياطي | fallback    |

### Proposed replacement (CRITICAL — needs validator review)

**KICKOFF directive:** "RELABEL 'موثوق' tier badge → coverage/sample-quality language ('تغطية بيانات جيدة' or similar)."

| Code | Arabic label (proposed) | English (proposed) |
|---|---|---|
| reliable    | تغطية بيانات جيدة     | good data coverage     |
| indicative  | تغطية محدودة          | limited coverage       |
| fallback    | تغطية غير كافية       | coverage insufficient  |

**Alternative phrasings to consider** (validators may suggest others):
- `بيانات وافرة` / `بيانات شحيحة` / `بيانات غير كافية`
- `عينة كافية` / `عينة محدودة` / `عينة غير كافية`
- `مستوى البيانات: جيد` / `محدود` / `غير كافٍ`

### Rationale

- **Why relabel:** `موثوق` ("reliable") is a strong claim about the *output* (the valuation is trustworthy). `تغطية بيانات جيدة` ("good data coverage") is a verifiable claim about the *input* (sample size and freshness). The latter is what we can defend.
- **Regulatory standard:** RICS Red Book VPS 6 §8 + IVS 106 §50 require *sample-size disclosure* but never authorise the AVM to certify its output as "reliable" — that's the role of a licensed valuer.
- **What the new labels do NOT claim:** that the *valuation* is reliable. They claim the *data behind it* meets a coverage threshold (n≥20 from §5.3).

### Prompt to validators

```
Review this Arabic tier-badge relabelling for a Qatar real-estate AVM (Automated
Valuation Model) platform. The badges currently describe the confidence of an
automatically-produced valuation; they are visible on every report card.

CURRENT BADGES:
  reliable   → "موثوق"
  indicative → "إرشادي"
  fallback   → "احتياطي"

PROPOSED REPLACEMENT:
  reliable   → "تغطية بيانات جيدة"      (good data coverage)
  indicative → "تغطية محدودة"           (limited coverage)
  fallback   → "تغطية غير كافية"        (coverage insufficient)

RATIONALE: The platform is an automated screening tool, not a licensed valuer.
"موثوق" claims trustworthiness of the OUTPUT; the new badges describe the
INPUT (sample size / data coverage). Per RICS Red Book VPS 6 §8 the platform
must disclose sample size but cannot certify its own output as reliable.

Please assess:
(a) Regulatory/legal soundness: does the new labelling reduce exposure for the
    platform vs. the current "موثوق"?
(b) Clarity for a non-expert Arabic reader (Modern Standard Arabic register,
    Qatari/Gulf usage acceptable).
(c) Any of the three proposed labels that could be misread or that have a
    better alternative.
(d) Whether to keep "إرشادي" / "احتياطي" elsewhere in the platform (they
    appear in other contexts) or whether the new vocabulary should unify all
    confidence-style labels across the product.

APPROVED / FLAGGED / REVISE — propose alternative wording where useful.
```

### Validator responses

**GPT-5:** _(paste here)_

**Gemini:** _(paste here)_

**Decision:** _(2 approvals → commit + Phase 1 grep to find all label sites)_

---

## §4. C4 — `ليس تقييماً معتمداً وفق RICS/IVS` reframe (8 sites)

### Original text (verbatim — two variants in production)

**Long form** (3 sites: `api.py:785`, `evaluate_v3.py:356`, `evaluate_property.py:474`):
> ثمّن يجمع البيانات السوقية من المصادر الحكومية والإعلانات النشطة. هذا تحليل معلوماتي للقرار، **وليس تقييماً عقارياً معتمداً وفق RICS/IVS**. للأغراض الرسمية (قروض، محاكم، تقارير محاسبية) يلزم مُقيِّم معتمد.

**Short form** (5 sites in `evaluate_unified.py`: 1956, 2394, 2608, 2714, 2847):
> ثمّن يجمع البيانات السوقية من المصادر الحكومية والإعلانات النشطة. هذا تحليل معلوماتي، **وليس تقييماً معتمداً وفق RICS/IVS**.

**List-item form** (`api.py:843` — `what_thammen_does_not[0]`):
> لا يُصدر تقييماً عقارياً معتمداً (RICS/IVS)

### Proposed replacement (per KICKOFF directive)

KICKOFF said: *"REFRAME 'ليس تقييمًا عقاريًا معتمدًا وفق IVS/RICS' → 'ولا يُعتبر تقرير تثمين رسمي صادر عن مثمّن مرخّص وفق معايير RICS/IVS'"*

**Long form replacement:**
> ثمّن يجمع البيانات السوقية من المصادر الحكومية والإعلانات النشطة. هذا تحليل معلوماتي للقرار، **ولا يُعتبر تقرير تثمين رسمي صادر عن مثمّن مرخّص وفق معايير RICS/IVS**. للأغراض الرسمية (قروض، محاكم، تقارير محاسبية) يلزم مُقيِّم معتمد.

**Short form replacement:**
> ثمّن يجمع البيانات السوقية من المصادر الحكومية والإعلانات النشطة. هذا تحليل معلوماتي، **ولا يُعتبر تقرير تثمين رسمي صادر عن مثمّن مرخّص وفق معايير RICS/IVS**.

**List-item form replacement:**
> لا يُصدر تقرير تثمين رسمي صادر عن مثمّن مرخّص وفق معايير RICS/IVS

### Rationale

- **The semantic shift:** from "this is NOT a certified RICS/IVS valuation" (defensive negation of a claim we never made) to "this is not a formal valuation report issued by a licensed valuer per RICS/IVS standards" (precise descriptive statement about provenance + author).
- **Why the new phrasing is safer:**
  - It NAMES the role we are NOT performing (`مثمّن مرخّص` — licensed valuer).
  - It NAMES the artefact we are NOT producing (`تقرير تثمين رسمي` — formal valuation report).
  - The current phrasing risks the reader inferring that the platform's output *could* be certified if it tried; the new phrasing makes clear the platform is structurally a different artefact.
- **Pairs with C3:** Replacing `موثوق` (output-claim) with `تغطية بيانات جيدة` (input-claim) PLUS reframing the disclaimer from "we don't certify" to "we're not the kind of thing that certifies" — both move the platform's self-description toward an honest screening-tool register.

### Prompt to validators

```
Review this Arabic disclaimer reframing for a Qatar real-estate AVM platform.
The disclaimer appears in every valuation report and on the /api/about endpoint.

ORIGINAL TEXT (long form, appears in 3 files):
"ثمّن يجمع البيانات السوقية من المصادر الحكومية والإعلانات النشطة. هذا تحليل
معلوماتي للقرار، وليس تقييماً عقارياً معتمداً وفق RICS/IVS. للأغراض الرسمية
(قروض، محاكم، تقارير محاسبية) يلزم مُقيِّم معتمد."

PROPOSED REPLACEMENT (long form):
"ثمّن يجمع البيانات السوقية من المصادر الحكومية والإعلانات النشطة. هذا تحليل
معلوماتي للقرار، ولا يُعتبر تقرير تثمين رسمي صادر عن مثمّن مرخّص وفق معايير
RICS/IVS. للأغراض الرسمية (قروض، محاكم، تقارير محاسبية) يلزم مُقيِّم معتمد."

(Short form is identical reframing with the trailing sentence removed.
 List-item form: original "لا يُصدر تقييماً عقارياً معتمداً (RICS/IVS)"
 replaced with "لا يُصدر تقرير تثمين رسمي صادر عن مثمّن مرخّص وفق معايير
 RICS/IVS".)

RATIONALE: The original phrasing is a defensive negation ("this is NOT a
certified valuation") that could imply the platform is the kind of thing that
could be certified if it tried. The replacement is a descriptive claim about
provenance + author ("this is not a formal valuation report issued by a
licensed valuer per RICS/IVS standards") — making clear the platform is
structurally a different artefact (an AVM screening tool, not a valuer's report).

Please assess:
(a) Regulatory/legal exposure in both versions. Qatari real-estate
    professional-services law context if relevant.
(b) Whether "مثمّن مرخّص" is the correct Qatari/Arabic term for "licensed
    valuer" in this regulatory context. Alternatives: "مُقيِّم معتمد",
    "مُقيِّم مرخّص"?
(c) Whether "تقرير تثمين" or "تقرير تقييم" is the more precise term for
    "valuation report" in the Qatari real-estate context.
(d) Clarity for a non-expert Arabic reader.

APPROVED / FLAGGED / REVISE — propose alternative wording where useful.
```

### Validator responses

**GPT-5:** _(paste here)_

**Gemini:** _(paste here)_

**Decision:** _(2 approvals → commit all 8+ sites)_

---

## §5. C5 — Buyer-prescriptive negotiation note reframe

### Original text (verbatim, surfaced at `brief.sections[0].content.note` in anchors 56_565_21 and 70_300_25)

> لا تدفع أكثر من وسيط MoJ + 10%. ابدأ بعرض أقل 10% من التقييم.

### Origin: pending Phase 1 grep (anticipated: `output_briefs.py` negotiation section builder)

### Proposed replacement

> المشترون في السوق الحالي عادةً لا يتجاوزون وسيط ‎MoJ‎ بأكثر من 10٪، وعروض الافتتاح تميل إلى أن تكون أقل من التقييم بنحو 10٪.

(Latin token `MoJ` LRM-wrapped per Pattern A discipline, even though this is a different commit — consistent style.)

### Rationale

- **Semantic shift:** from imperative (`لا تدفع`, `ابدأ بعرض`) to descriptive (`المشترون ... عادةً لا يتجاوزون`, `عروض الافتتاح تميل ...`).
- **Why this matters:** the platform's own scope (see C4 §6.1 of Project_Instructions §10 Honesty Principles, principle 6) is "do not make the user's decision." Imperative language ("don't pay X") instructs the user; descriptive language ("typical buyers don't pay above X") informs them. The user remains the decider.
- **What this does NOT claim:** the platform doesn't tell the user what to do; it reports observed market behaviour patterns (n=? per the underlying MoJ + asking-side empirical findings, EMPIRICAL_FINDINGS §3).
- **Numerical content preserved:** the 10% ceiling and 10% offer discount are unchanged — these are the project's hard ceilings per Project_Instructions §10. Only the imperative mood is reframed.

### Prompt to validators

```
Review this Arabic-text reframing for a Qatar real-estate AVM platform. The
text appears in the "negotiation range" section of buyer-facing valuation
reports.

ORIGINAL TEXT:
"لا تدفع أكثر من وسيط MoJ + 10%. ابدأ بعرض أقل 10% من التقييم."

PROPOSED REPLACEMENT:
"المشترون في السوق الحالي عادةً لا يتجاوزون وسيط MoJ بأكثر من 10٪، وعروض
الافتتاح تميل إلى أن تكون أقل من التقييم بنحو 10٪."

RATIONALE: The original uses imperatives ("don't pay", "start with an offer")
that instruct the user. The replacement is descriptive — it reports observed
market behaviour patterns rather than directing the user's decision. The
platform's own policy (per its founding "honesty principles") forbids making
the user's decision. The numerical thresholds (10% above MoJ median ceiling,
10% offer discount) are unchanged.

Please assess:
(a) Whether the descriptive reframing successfully removes the imperative
    register while preserving the substantive guidance.
(b) Modern Standard Arabic register / Gulf Arabic usage for "عروض الافتتاح"
    (opening offers) — is there a more natural Qatari phrasing?
(c) Any regulatory/legal exposure with the descriptive claim "المشترون عادةً
    لا يتجاوزون..." — does this make a claim about typical buyer behaviour
    that the platform needs to be able to defend with data?
(d) Whether using "٪" (Arabic percent sign) vs "%" is preferred in Qatari
    professional usage.

APPROVED / FLAGGED / REVISE — propose alternative wording where useful.
```

### Validator responses

**GPT-5:** _(paste here)_

**Gemini:** _(paste here)_

**Decision:** _(2 approvals → commit)_

---

## §6. B — `classifier_failure` new refusal trigger

### New refusal template (proposed)

Insert as 7th key in `refusal_templates.REFUSAL_TEMPLATES`:

```python
'classifier_failure': {
    'message_ar': (
        'لم نتمكّن من تحديد نوع العقار من البيانات الحكومية المتاحة. '
        'قد يكون العنوان غير مفهرس حالياً في قاعدة QARS أو خارج نطاق '
        'التغطية. نوصي بالتحقّق من بيانات العنوان أو التواصل معنا إذا '
        'كانت المُدخَلات صحيحة.'
    ),
    'message_en': (
        'We could not classify this property from available government '
        'data. The address may not yet be indexed in QARS, or may fall '
        'outside current coverage. Please verify the address details, '
        'or contact us if the entered values are correct.'
    ),
    'recommendation_ar': 'تحقّق من بيانات العنوان أو تواصل معنا.',
},
```

### Dispatcher change (proposed) in `evaluate_unified._compute_refusal_reason()`

Insert as the new **row 2** (between current row 1 and current row 2):

```python
# 2. classifier_failure — engine could not classify the property at all
#    (QARS lookup returned 0 features; asset_type fell back to 'unknown').
#    Distinct from spatial_ambiguity (row 3, formerly row 2) which fires
#    when the asset_type_reality_stop path STOPS the engine after a
#    successful classification. Distinct from comp_density_sparse (row 7)
#    which assumes we know the asset type but lack MoJ comparables.
if asset_type == 'unknown' and method != 'asset_type_reality_stop':
    return get_refusal_template('classifier_failure', **base_ctx)
```

All subsequent rows renumber: spatial_ambiguity becomes row 3, asset_scale_extreme row 4, asset_class_out_of_scope row 5, regime_shift row 6, comp_density_sparse default row 7.

### Rationale

- **What changes:** anchor 70/300/25 (asset_type='unknown', district=null, plot_area_m2=null) currently fires `comp_density_sparse` ("fewer than 5 comparable transactions") which is **factually misleading**. The real failure is **QARS coverage gap** — the engine doesn't even know what type of property is at the address. New trigger emits the truthful refusal CTA.
- **What stays:**
  - All 6 existing templates unchanged.
  - All other dispatcher rows unchanged (their precedence ordering preserved relative to each other).
  - Test coverage from Sprint 2.22.0a/5 unchanged.
- **Templates count:** 6 → 7 active triggers. CHANGELOG amends KICKOFF F5 footer.

### Prompt to validators

```
Review this Arabic + English refusal-template text for a Qatar real-estate AVM
platform. The text appears when the engine cannot classify a submitted address
(the property type is "unknown" because the upstream Qatar GIS / QARS service
returned no features for the address).

PROPOSED REFUSAL TEMPLATE — Arabic:
message_ar:
"لم نتمكّن من تحديد نوع العقار من البيانات الحكومية المتاحة. قد يكون العنوان
غير مفهرس حالياً في قاعدة QARS أو خارج نطاق التغطية. نوصي بالتحقّق من بيانات
العنوان أو التواصل معنا إذا كانت المُدخَلات صحيحة."

recommendation_ar:
"تحقّق من بيانات العنوان أو تواصل معنا."

PROPOSED REFUSAL TEMPLATE — English:
message_en:
"We could not classify this property from available government data. The
address may not yet be indexed in QARS, or may fall outside current coverage.
Please verify the address details, or contact us if the entered values are
correct."

CONTEXT: This message replaces a generic "fewer than 5 comparable transactions"
template that previously fired on this case. The new template is intended to
distinguish the user-facing CTA for cases where the engine cannot even
determine what the property IS (vs. cases where it knows the property type but
lacks comparable transactions).

Please assess:
(a) Regulatory/legal soundness — does the platform expose itself by saying it
    couldn't classify? Is naming "QARS" (the upstream service) acceptable, or
    should the message stay vendor-neutral?
(b) Whether "غير مفهرس" (not indexed) is the correct Modern Standard Arabic
    term, or whether "غير مُسجّل" (not registered) / "غير مُدرَج" (not listed)
    is better.
(c) Whether mentioning "نطاق التغطية" (coverage scope) accurately describes
    what the platform supports.
(d) Whether the recommendation ("verify or contact us") is appropriately
    non-prescriptive while still actionable.

APPROVED / FLAGGED / REVISE — propose alternative wording where useful.
```

### Validator responses

**GPT-5:** _(paste here)_

**Gemini:** _(paste here)_

**Decision:** _(2 approvals → commit refusal_templates.py + dispatcher change)_

---

## §7. B2/B3 architecture confirmation — Anas decision (NOT a multi-AI item)

### The question Anas asked

> "Before any further commits: confirm in writing whether the B2/B3 unification is intentional (i.e., `classifier_failure` subsumes both my KICKOFF cases) or an oversight that needs a separate `coverage_gap` trigger."

### My analysis (Claude Code)

KICKOFF Pattern B requested 3 user-facing refusal cases:

| KICKOFF case          | Semantic                                            |
|-----------------------|------------------------------------------------------|
| `data_missing`        | We know your property type, but MoJ comparables are too few |
| `classifier_failure`  | We could not determine what type of property your address points to |
| `coverage_gap`        | We know your district, but we explicitly do not yet cover it |

The Sprint 2.22.0a/5 dispatcher already has SIX triggers in its §5.3 precedence chain. Mapping KICKOFF's 3 cases to the existing engine:

| KICKOFF case        | Engine trigger             | Status |
|---------------------|----------------------------|--------|
| `data_missing`      | `comp_density_sparse`      | **EXISTING** — already correctly named + dispatched |
| `classifier_failure`| (none — falls to default)  | **NEW** — proposed §6 above |
| `coverage_gap`      | `density_gated_district`   | **EXISTING** — already correctly named + dispatched (Pearl etc.) |

So my Pattern B plan adds **1 new template + 1 new dispatcher row** (not 3 new templates), because `coverage_gap` and `data_missing` are already represented by named existing templates with correct dispatch rules.

### Why `classifier_failure` and `coverage_gap` MUST stay separate

Both involve "the engine can't produce a valuation for your address", but the *cause* — and therefore the right user CTA — differs:

|                                  | `classifier_failure`                                                  | `coverage_gap` (`density_gated_district`)                          |
|----------------------------------|------------------------------------------------------------------------|--------------------------------------------------------------------|
| **Cause**                        | Upstream QARS service returned 0 features for the submitted address.  | Engine deliberately excludes this district until data enrichment.  |
| **Engine's knowledge of address**| Doesn't know what's there.                                            | Knows the district perfectly (e.g. "Pearl"); knows it's excluded.  |
| **Right user CTA**               | "Verify the address — it may be a typo / unindexed / outside scope."  | "We're working on covering this area; please use a licensed valuer or check back." |
| **What the user can do next**    | Re-enter address, or contact us.                                       | No action will unlock coverage; use an alternative.                |
| **Engineering action triggered** | None (data quality is upstream — QARS owners). May log for follow-up. | Eventually: enrich coverage → flip the district off the gate list. |

Collapsing these into one trigger gives users the wrong CTA half the time:
- A Pearl user told "verify your address" is unhelpful — their address is perfectly correct, the platform just doesn't cover Pearl.
- A typo-or-unindexed user told "we're working on covering this area" is unhelpful — their problem is local to their address, not a coverage roadmap.

### My recommendation

**KEEP THEM SEPARATE.** My Pattern B plan does NOT unify B2/B3. The new `classifier_failure` trigger handles the `asset_type='unknown'` case (typo/unindexed/QARS-coverage); the existing `density_gated_district` trigger handles the deliberate-district-exclusion case. Each has its own dispatcher row, its own template, its own user CTA.

### Anas decision

Please mark one before B implementation proceeds:

- [x] **ACCEPT** my recommendation (keep classifier_failure and coverage_gap separate; my §6 plan stands as-is).
  - **Marked 2026-05-27 by Anas** (chat message: "i mark accept").
  - **Architecture is now LOCKED:** Pattern B adds exactly 1 new template
    (`classifier_failure`) + 1 new dispatcher row in
    `_compute_refusal_reason()`. The existing `density_gated_district`
    trigger (KICKOFF's "coverage_gap") stays untouched.
  - **Still pending** before Pattern B commit can land: multi-AI consensus
    on the Arabic + English message strings in §6 above (the
    classifier_failure template copy). Architecture decided ≠ copy
    approved.
- [ ] ~~**OVERRIDE** my recommendation (unify them; I'll redesign Pattern B accordingly).~~
- [ ] ~~**DEFER** B to a separate Sprint while C1/C3/C4/C5 ship in 2.22.0a.2 (Pattern B is the largest regression surface — splitting it is allowed under Rule #38).~~

If you accept, the commit order in §6 above is canonical: B ships LAST after all C-pattern validations land.

---

## End-of-batch summary

| § | Pattern | Type of change       | Validation | Estimated edit footprint |
|---|---------|----------------------|------------|--------------------------|
| 1 | C1      | Prose neutralization | Multi-AI   | ~15 lines, 2 files       |
| 2 | C2 part 2 | Caveat rewrite     | Multi-AI   | ~5 lines, 1 file         |
| 3 | C3      | Tier badge relabel   | Multi-AI   | TBD per Phase 1 grep     |
| 4 | C4      | Disclaimer reframe   | Multi-AI   | ~10 lines, 4 files       |
| 5 | C5      | Imperative → descriptive | Multi-AI | ~6 lines, ~1 file       |
| 6 | B       | New trigger + dispatcher row | Multi-AI | ~25 lines, 2 files |
| 7 | B2/B3 architecture | Decision (not multi-AI) | Anas direct | n/a |

Once §7 is decided AND §§1–6 have two-AI approvals each, the commit cascade proceeds in KICKOFF order (C1 → C3 → C4 → C5 → B). Each lands as an atomic single-purpose commit per Rule #38.

---

*Sprint 2.22.0a.2 multi-AI validation batch packet. Rule #54 compliance.*

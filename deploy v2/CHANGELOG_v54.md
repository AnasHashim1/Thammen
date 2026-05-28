# CHANGELOG v54 — Sprint 2.22.0a.3: Arabic Surface Honesty Pass

**Sprint:** 2.22.0a.3 (reworked after first push-block — see "Reopen log" below)
**Engine version:** `thammen-sprint2p22p0a3-arabic-surface-honesty`
**Sprint tag:** `2.22.0a.3`
**Files touched:** `evaluate_unified.py` (T1.1 + T1.2 + T1.2 LRM +
T1.3 + T1.4 + T2.5 + ENGINE_VERSION + new `_get_moj_freshness_tier`
helper), `stock_strata.py` (T1.4), `reasoning_trace.py` (T2.7 deduped
+ T-mzad), `api.py` (T-mzad ×3 sites), `index.html` (T1.3 + T2.5 +
T1.2 frontend headline reframe), `docs/Operational_Rules.md` (Rule #25
detector regex: separator class extended with EN-DASH for year-range
tokens), `test_sprint_2p22p0a2_c2_mechanical.py` (T1.4 test alignment),
`run_sprint_2p22p0a_suite.py` (pre-existing-drift gate bump 386 → 392),
new `test_sprint_2p22p0a3_surface_honesty.py` (43 assertions, of which
4 are LRM sentinels), new `docs/MULTI_AI_VALIDATION_BATCH_2p22p0a3.md`,
this CHANGELOG.
**Push status:** **STOP** — push consent reserved for Anas (Rule #32).
**Multi-AI validation:** drafted at
[`docs/MULTI_AI_VALIDATION_BATCH_2p22p0a3.md`](docs/MULTI_AI_VALIDATION_BATCH_2p22p0a3.md),
runs PENDING (Anas) — Question B IS the MUC-trend gate, validating
the corrected design (not the original undersized one).

---

## Reopen log (why this Sprint was reworked)

Original commit `3c3f6a9` shipped 6 items with what looked like clean
green tests. Anas's review caught a fundamental flaw in T1.2:

- **Original gate:** `level in ('critical','high')`
- **Original rationale:** "matches Amendment A — 56/565/21 (level=
  moderate, slope=+1.9%) keeps the numeric trend"
- **Reality:** Anas had RETRACTED Amendment A after my own audit
  proved 56/565/21 was MUC-active at `moderate` AND showed the
  contradictory `استقرار 1.9%/سنة` trend headline. With MoJ data at
  148-day staleness parking ~every address at `moderate`, the
  high/critical-only gate was a no-op in production. The named
  contradiction case was the bug the gate was supposed to fix, and
  it never fired there.

The retracted-rationale-still-in-CHANGELOG was also a tell that I'd
shipped the implementation without re-checking against the retraction.
This is recorded here so future Sprint reviews catch the same class of
error sooner: when a stated rationale references a "matches Amendment
X" pattern, verify Amendment X is still standing before shipping.

Two additions surfaced at the same review:

- **Mzad** — `reasoning_trace.disclaimer` listed Mzadqatar as an
  active-listings source. Mzadqatar is permanently excluded from
  Thammen's data pipeline (T5 — auction-only). Listing it claimed a
  source we don't use — a live honesty bug, on-theme for this Sprint.
  Orphaned by T2.8 deferral.

- **T2.7 dedup** — initial pass added 4 villa-path legality items.
  The third item ("وضع التقسيم والفرز الرسمي") duplicated the
  standard-list line "أي التزامات قانونية ... حصص غير مفروزة" —
  redundant. The fourth item collapsed two distinct concerns
  (occupancy state + lease disclosure); Anas's intended item is
  occupancy-completion-certificate verification (OCCERT) as a
  distinct municipal-records check.

**Post-validation fold (Rule #54).** The Sprint reopened a second
time after the multi-AI validation batch
([docs/MULTI_AI_VALIDATION_BATCH_2p22p0a3.md](docs/MULTI_AI_VALIDATION_BATCH_2p22p0a3.md))
returned:

- **C (T1.4 wording)** — both GPT and Gemini flagged the prior
  "كعبء معماري" framing (GPT: provocative to owners / developers /
  valuers; Gemini: implies universality). The shipped reframe also
  still read as a restated rule (flat present-tense). Refold:
  TENDENCY prose at the long-form site
  (`غالباً ما تتراجع مساهمة البناء في القيمة مع تقادم العقار السكني
  دون تجديد، فتصبح الأرض المكوّن الأكبر في التسعير`), short
  descriptive tag at the regime-label + stratum-description sites
  (`نمط سوقي: غلبة قيمة الأرض في العقارات القديمة`). No 'قاعدة',
  no 'عبء'.

- **D (T2.5 wording)** — GPT pushed back on the vague "بشكل
  ملحوظ" replacement: don't trade a fake-precise range for vague
  wording, give causal + specific. Refold names the inputs that
  would actually move the estimate
  (`قد يؤدي إدخال التفاصيل الفعلية للعقار — كالحالة والمساحة
  الدقيقة والتشطيبات — إلى تعديل جوهري في التقدير`). Pairs with
  T1.1: T1.1 dropped the unsupported condition claim; T2.5 here
  names condition as exactly what would refine the estimate if
  provided.

These are the validators' own refinements (GPT on both, Gemini on
C's scope) — no re-validation needed, just record. **Reconciliation
note on T1.2** (Question B in the batch): the shipped gate is
**staleness-coupled** (`tier in ('stale','very_stale') OR level in
('high','critical')`), strictly more conservative than the
question's framing (which asked about MUC level alone). Both
models' Question-B feedback is satisfied-or-exceeded by the
shipped design — no further fold needed there.

This CHANGELOG is the corrected + post-validation-folded design.
Engine version unchanged
(`thammen-sprint2p22p0a3-arabic-surface-honesty`); commit
`3c3f6a9` was amended to `e7cc19a` for the gate rework, and to
`4c8e015` for the LRM pre-push fix; the C/D fold amends `4c8e015`
in lockstep so the final master history reflects the corrected +
folded implementation as a single Sprint.

---

## Why this Sprint

Epistemic-humility consistency on the user-visible Arabic surface.
Live brief snapshot of `56/565/21` ([`docs/phase0/brief_56_565_21.strings.txt`](docs/phase0/brief_56_565_21.strings.txt))
surfaced six over-claims where the engine asserts more than it
knows; a seventh (Mzad) surfaced in review:

1. **Fabricated condition claim** — `بحالة جيدة` on the building
   decomposition's normal branch. Zero condition ground truth.
2. **MUC ↔ numeric-trend contradiction** — `trend.slope_pct = 1.89`
   alongside a `وزارة العدل ... 2025-12-31` staleness banner = a
   precise yearly rate defended on data that pre-dates the rate's
   end-of-window.
3. **"تقييم كامل" UI label** — implies a formal valuation product.
4. **"10-Year Rule" named-rule framing** — `قاعدة الـ 10 سنوات` /
   `قاعدة الـ10-Year-Rule`. No published rule.
5. **`±20-40%` ungrounded range** — claims a calibration study we
   never ran.
6. **Villa-path `known_unknowns` missing Qatar legality gaps** —
   common Qatari sources of post-sale dispute not surfaced.
7. **Mzad source-list lie** — disclaimer claims a source we don't use.

Two items from the original kickoff still NOT in this Sprint:

- **T2.6** (`شواهد كافية` → `شواهد سوقية كافية`) **DROPPED**: would
  modify Sprint 2.22.0a.2 Pattern C3 taxonomy that was just
  AI-validated and Anas-locked. Defer until C3 stabilizes.
- **T2.8** (disclaimer 4→2 consolidation) **DEFERRED to 2.22.0a.4**:
  the 4 layers require a separate brief-rendering audit. Single-
  purpose (Rule #38). Multi-AI Question E retained so the answer
  informs the 2.22.0a.4 design.

---

## What this Sprint ships (7 items — 6 from original + Mzad)

### T1.1 — Drop `بحالة جيدة` fabricated claim

[`evaluate_unified.py:1148`](evaluate_unified.py#L1148) (`_decompose_value`,
normal branch `0.15 ≤ bld_pct < 0.35`).

**Before:**
```python
interp = (f'البناء يساهم بنسبة {bld_pct*100:.1f}% من القيمة — '
          f'مساهمة طبيعية لبناء بحالة جيدة على هذه الأرض.')
```

**After:**
```python
interp = (f'البناء يساهم بنسبة {bld_pct*100:.1f}% من القيمة — '
          f'مساهمة ضمن النطاق النموذجي لمبنى على هذه الأرض.')
```

### T1.2 — STALENESS-COUPLED gate (reworked from high/critical-only)

[`evaluate_unified.py:4155-4225`](evaluate_unified.py#L4155) +
new helper [`_get_moj_freshness_tier()`](evaluate_unified.py#L520)
near the cache section + frontend headline reframe at
[`index.html:1075-1090`](index.html#L1075).

**Corrected gate:**
```python
_muc_level = (output.get('material_uncertainty') or {}).get('level')
_fresh_tier = _get_moj_freshness_tier()
_suppress_slope = (
    _fresh_tier in ('stale', 'very_stale')   # ≥91 days old
    or _muc_level in ('high', 'critical')
)
```

**Output shape when suppressed:** label + years[] backing detail +
`historical_window_ar` ("نافذة 2020–2025") + `suppressed_reason_ar`
(transparency: names the active cause). Drops `slope_pct` AND the
`%/سنة` exceptional-slope warning.

**Output shape when retained** (fresh + low — rare today): same as
the original behaviour + `slope_pct` rounded to 1 decimal +
`historical_window_ar` as backing.

**Self-healing:** when MoJ publishes a fresh bulletin, the gate
auto-clears (no code change). The freshness cache uses a process-
lifetime singleton; restart on cron-replaced CSV picks up `fresh`.

**Why NOT `level != 'low'` as the gate:** `moderate` MUC is NOT
purely staleness-derived. The `assess_uncertainty` scorer in
[`material_uncertainty.py:295-310`](material_uncertainty.py#L295)
assigns score=2 to (a) `rent_n=None` (most calls), (b)
`has_field_inspection=False` (every desktop call). Either alone
promotes to `moderate`. Coupling on `moderate` would over-suppress
the (rare) fresh+low-MUC case where the slope IS defensible.

**Frontend headline reframe** (matches kickoff's spec example
`'اتجاه تاريخي: استقرار — نافذة ٢٠٢٠–٢٠٢٥'`):
- When `tr.slope_pct != null` → `اتجاه السوق: <label> (<X.X>%/سنة)`
  (original behaviour, slope retained path)
- When `tr.slope_pct == null && tr.historical_window_ar` →
  `اتجاه تاريخي: <label> — <window>` (NEW — suppressed path)
- Else → `اتجاه السوق: <label>` (defensive fallback)

**Float-noise rounding:** `1.8900000000000001 → 1.9` via
`round(slope_pct, 1)` (was a kickoff Tier 1 minor; included since
the block was already being edited).

**LRM bidi-wrap (pre-push fix-what-you-broke).** The new T1.2
strings embed LTR runs inside Arabic — the year-range
(`2020–2025`) in `historical_window_ar`, and the day-count
(`91`) in the staleness branch of `suppressed_reason_ar`. Without
U+200E (LRM) bracketing under `dir="rtl"` they can visually
reverse — same bidi class as the historic `31/918/99 → 99/918/31`
documented in Operational_Rules #25. Wrap added on both sides,
matching the existing `muc_clause_ar` convention
(`‎VPGA 10‎`, `‎effective 31 January 2025‎`, etc.). The MUC-branch
`suppressed_reason_ar` is pure Arabic (uses `عالٍ/حرج`, not Latin
level names) — no wrap added there; defensive test enforces this.
Operational_Rules #25 detector regex separator class extended
with EN-DASH (U+2013, the "range dash") — without it the
year-range token would not have triggered the detector's
"needs LRM" branch, since `-` (hyphen-minus, already in class)
covers ISO dates but not range expressions. Pre-existing residual
LRM issues (`52/903/90`, the bare ISO dates in `note_ar`, the
`RICS/IVS` runs in `.disclaimer`) stay deferred on the 2.22.0a.1
hotfix track — fix-what-you-broke scope discipline.

### T1.3 — `تقييم كامل` → `تحليل آلي` (3 sites)

[`index.html:822`](index.html#L822) (UI badge) +
[`evaluate_unified.py:1886`](evaluate_unified.py#L1886) +
[`:1945`](evaluate_unified.py#L1945).

### T1.4 — "10-Year Rule" → observed tendency (3 sites)

[`evaluate_unified.py:1135, 3687`](evaluate_unified.py#L1135) +
[`stock_strata.py:96-97`](stock_strata.py#L96).

**Long-form prose (interp at eu.py:1135 land_dominant branch):**
TENDENCY framing — `غالباً ما تتراجع مساهمة البناء في القيمة مع
تقادم العقار السكني دون تجديد، فتصبح الأرض المكوّن الأكبر في
التسعير`. Leaves room for exceptions (modernised old villas,
luxury renovations) and avoids the restated-rule register.

**Short descriptive tag (regime_label at eu.py:3687 + stratum
description at stock_strata.py:96):** `نمط سوقي: غلبة قيمة الأرض
في العقارات القديمة`. No 'قاعدة', no 'عبء' — both flagged by
GPT + Gemini in the multi-AI validation batch.

Internal regime constant `'qatar_10_year_rule'` preserved (dispatch
key, not user-visible). Sprint 2.22.0a.2 §9 softening at
[`_ten_year_rule_disclosure_ar`](evaluate_unified.py#L828) preserved
verbatim (guard test asserts).

**Test-alignment side-effect:** Sprint 2.22.0a.2 Pattern C2 test
assertion updated TWICE in lockstep — first to use the initial T1.4
phrasing (replacing the `'10-Year-Rule'` literal), then to the
post-validation short-tag wording. Closed-Sprint test-anchor
maintenance, not closed-case re-opening (Rule #53).

### T2.5 — `±20-40%` → causal + specific (2 sites)

[`evaluate_unified.py:3757`](evaluate_unified.py#L3757) (backend MU
factor) + [`index.html:1049`](index.html#L1049) (frontend disclaimer
card). Both now say:

> قد يؤدي إدخال التفاصيل الفعلية للعقار — كالحالة والمساحة الدقيقة
> والتشطيبات — إلى تعديل جوهري في التقدير.

Causal + specific framing per GPT validation feedback: don't replace
fake-precise (`±20-40%`) with vague (`بشكل ملحوظ`) — name the
inputs that would move the estimate (condition, exact area,
finishes). Pairs with T1.1: T1.1 dropped the fabricated condition
claim; T2.5 names condition as exactly what would refine the
estimate if provided. Both strings pure Arabic, em-dashes between
Arabic words — no LRM exposure.

### T2.7 — Qatar legality gaps in villa-path `reasoning_trace.known_unknowns`

[`reasoning_trace.py:377-389`](reasoning_trace.py#L377) — extend the
`('villa_standalone', 'villa_compound')` block with **3** items
(deduped from initial 4):

1. تعديلات غير مرخصة من البلدية على البناء الأصلي
   (unauthorized modifications)
2. ملاحق وإضافات غير موثقة في السجل العقاري
   (undocumented extensions)
3. التحقق من شهادة إتمام الإشغال / شهادة إنجاز البناء من البلدية
   (OCCERT / municipality occupancy-completion certificate)

**Dedup rationale:** the original 4th item ("وضع التقسيم والفرز
الرسمي") duplicated the standard-list line
`"أي التزامات قانونية (رهون، خلافات، إرث، حصص غير مفروزة)"` — the
"حصص غير مفروزة" phrase already covers subdivision/parcellation
status. A guard test asserts the dropped item is NOT re-added AND
that the standard-list coverage remains.

Frontend wiring confirmed: [`index.html:1225`](index.html#L1225)
reads from `reasoning_trace.known_unknowns` — items render
automatically, no frontend change needed.

### T-mzad — Drop Mzadqatar from user-visible source lists (live honesty bug)

3 disclaimer sites + 1 sources-used array entry:

- [`reasoning_trace.py:113`](reasoning_trace.py#L113) — `ReasoningTrace.disclaimer` default
- [`api.py:841`](api.py#L841) — `/api/disclaimer` `disclaimer_ar`
- [`api.py:849`](api.py#L849) — `/api/disclaimer` `disclaimer_en`
- [`api.py:888`](api.py#L888) — `/api/about` `data_sources.listings[]` array entry

Mzadqatar is permanently excluded from Thammen's data pipeline (T5
auction-only). Listing it claimed a source we don't use. FGRealty +
PropertyFinder + arady are valid T2 sources and remain.

---

## Decisions made (logged inline)

Anas's "do whatever you deem is the right thing" delegation +
post-review correction:

| Q | Decision | Rationale |
|---|---|---|
| Q1 — T1.2 gate (**REWORKED**) | `tier in ('stale','very_stale') OR level in ('high','critical')` | Self-healing form. Anas's preferred shape. `level != 'low'` rejected after confirming `moderate` is NOT purely staleness-derived (`has_field_inspection=False` always = score 2). |
| Q2 — T2.7 wiring target | `reasoning_trace.known_unknowns` via `add_standard_unknowns()` | Frontend renders from this field, not from `material_uncertainty.known_unknowns_ar`. |
| Q3 — T2.8 layer strategy | DEFER to 2.22.0a.4 | Needs separate brief-rendering audit. |
| Q4 — Live string capture | Skip the curl | Code is source-of-truth. Avoids 22s+503 risk. |
| Q5 — T2.7 dedup | 4 items → 3 (subdivision dropped; OCCERT distinct concern) | Subdivision covered by standard list's "حصص غير مفروزة" — no duplication. OCCERT is a distinct municipal-records verification. |
| Q6 — T-mzad scope | All 4 user-visible sites | Disclaimer parity (Ar+En) + the sources-used array. Internal listing-module references stay (dead-code Mzad is operational debt, separate concern). |
| Q-C — T1.4 post-validation fold | Tendency prose + short descriptive tag | GPT+Gemini both flagged "كعبء معماري". Tendency framing (`غالباً ما تتراجع...`) leaves room for exceptions; short tag (`نمط سوقي: غلبة قيمة الأرض...`) on label sites avoids cramming the full sentence. |
| Q-D — T2.5 post-validation fold | Causal + specific replacement | GPT: vague replacement under-delivers. Name the actionable inputs (condition / exact area / finishes) — pairs with T1.1's condition-claim removal. |

The **retracted Q1 "matches Amendment A" rationale** that shipped in
the original `3c3f6a9` is permanently removed from this CHANGELOG.

---

## Tests

### New: `test_sprint_2p22p0a3_surface_honesty.py` — 45/45 PASS

Substring checks against source files + functional checks (Rule E14
— exercise production logic, not echo input). The functional T1.2
helper replays the production gating block verbatim (including the
LRM wraps), parameterized on both `freshness_tier` and `muc_level`.

| Coverage | Tests |
|---|---|
| T1.1 | 2 |
| T1.2 (rework) | 13 (suppression: 4 — stale/very_stale/high/critical; retention: 3 — fresh+low / mild+low / fresh+moderate; rounding + window-format + 4 production-source pins) |
| T1.2 LRM sentinels | 4 (window LRM-bracketed; staleness `91` LRM-bracketed; MUC-branch pure-Arabic NO LRM over-wrap; Operational_Rules #25 detector regex includes EN-DASH) |
| T1.3 | 3 |
| T1.4 (post-fold) | 5 (named_rule absent + tendency phrasing present + provocative-burden GONE + §9 softening preserved + internal regime constant preserved) |
| T2.5 (post-fold) | 5 (quantitative range absent ×2 + causal phrase present ×2 + prior vague phrasing GONE) |
| T2.7 (deduped) | 7 (3 items in villa_standalone/villa_compound; subdivision-NOT-re-added guard; subdivision-covered-by-standard guard; NOT in apartment; pre-existing villa items preserved; standard items preserved) |
| T-mzad | 4 (3 disclaimers + 1 sources-used array) |
| Out-of-scope guards | 2 (C3 + C4 protection) |
| **Total** | **45/45 PASS** |

Run:
```
PYTHONIOENCODING=utf-8 python test_sprint_2p22p0a3_surface_honesty.py
```

### Aggregator gate update: `run_sprint_2p22p0a_suite.py`

Pre-existing drift caught: `test_sprint_2p22p0a_refusal_reason.py`
had 115 assertions but the gate expected 109 (origin: Sprint
2.22.0a.2 Pattern B commit `3328926`). Bumped `EXPECTED_TOTAL`
386 → 392. Test-infrastructure-correctness maintenance.

### Sprint 2.22.0a.2 Pattern C2 test alignment

[`test_sprint_2p22p0a2_c2_mechanical.py:34-39`](test_sprint_2p22p0a2_c2_mechanical.py#L34)
updated to assert T1.4-aligned phrasing. Test follows product state.

### Regression — all 4 harnesses GREEN

| Harness | Result | Wall time |
|---|---|---|
| `run_sprint_2p22p0a_suite.py` (pinned 392 aggregator) | **392/392 PASS** | 13.52s |
| `test_sprint_2p16p17_security.py` | **15/15 PASS** | <1s |
| Standalone 2.22.0a.1/.2/.3 tests (10 files) | All PASS | ~10s combined |
| `2p22p0_pre/run_regression_2p22p0a.py` (broader sweep) | **47/47 files PASS** | 92.6s |

(Re-run after the C/D post-validation fold — figures reproduced from actual command output, Rule #36.)

---

## Operational rules invoked

| Rule | How |
|---|---|
| **#11** Defensive endpoint design | The corrected T1.2 gate self-heals: when MoJ publishes fresh, the slope returns without code change. |
| **#32** Push & Commit Discipline | NO push without explicit consent. CHANGELOG ships `Push status: STOP`. Rework + amend authorized by Anas. |
| **#33** Empirical-First Audits | The Sprint reopen IS this rule applied — Anas's review measured the gate's actual effect vs the original "matches Amendment A" claim, and the measurement falsified the claim. |
| **#36** Observed-vs-Expected Reporting | The "148-day staleness" figure + the 39/39 test count + the 392/392 aggregator count are actual run output, not estimates. |
| **#38** Single-purpose Sprint | One theme (epistemic-humility). T2.8 deferred. T-mzad earned its slot — same theme, surfaced in the same review pass. |
| **#39** Deviation Justification | The Q-decisions (above) each follow the 3-sentence pattern: why this choice + what's lost + what user needs to know. The Q1 re-decision after the retraction is documented explicitly. |
| **#40** Replica + Production Verification | T1.2 functional tests replay production logic verbatim AND substring tests pin the production source to the corrected gate. T2.7 + T-mzad functional tests import `add_standard_unknowns` + `ReasoningTrace` directly. |
| **#42** Deferred-work documentation | T2.6 + T2.8 deferral conditions documented (this CHANGELOG + multi-AI doc). |
| **#53** Closed cases stay closed (as comparison anchors) | Sprint 2.22.0a.2 cited for context (Pattern B drift catch-up, Pattern C2 test alignment, C3 + C4 protection) — never as comparison foils. |
| **#54** Multi-AI Validation (REQUIRED) | Batch doc at `docs/MULTI_AI_VALIDATION_BATCH_2p22p0a3.md`. Validation runs PENDING **after** this rework (validating the corrected design, not the original wrong one). |
| **E14** Validation script exercises production logic | T1.2 + T2.7 + T-mzad functional tests call real production code. |

---

## Commits

Original commit `3c3f6a9` (the wrong-gate ship) will be **amended**
in lockstep with this CHANGELOG so the master history reflects the
corrected design as a single atomic Sprint commit. The amend is
authorized by Anas ("amend 3c3f6a9 or stack — your call, keep it
atomic"). Single Sprint = single commit matches Rule #38; the
in-flight rework is documented here in §"Reopen log" rather than
preserved as separate stacked commits.

If validation later requests more revisions, those become FOLLOW-UP
commits on top, not further amends.

---

## Deployment (push step, REQUIRES Anas consent)

```cmd
cd /d "C:\Thammen"
git subtree split --prefix "deploy v2" -b heroku-deploy-tmp-2p22p0a3
git push heroku heroku-deploy-tmp-2p22p0a3:master --force
git branch -D heroku-deploy-tmp-2p22p0a3
```

### Verification curl (post-push)

```cmd
curl -s https://thammen.qa/api/health
:: expect: "version":"3.1.0-sprint2.22.0a.3"
:: expect: "engine_version":"thammen-sprint2p22p0a3-arabic-surface-honesty"

curl -s -X POST https://thammen.qa/api/evaluate ^
  -H "Content-Type: application/json" ^
  -d "{\"zone\":56,\"street\":565,\"building\":21}"
:: expect (current 148-day MoJ staleness):
::   - NO "بحالة جيدة" anywhere
::   - NO "تقييم كامل" anywhere
::   - NO "قاعدة الـ 10 سنوات" or "قاعدة الـ10-Year-Rule" anywhere
::   - NO "±20-40%" anywhere
::   - NO "Mzad" in any disclaimer
::   - trend.slope_pct ABSENT (suppressed by stale MoJ)
::   - trend.label = "استقرار"
::   - trend.historical_window_ar = "نافذة 2020–2025" (or similar)
::   - trend.suppressed_reason_ar contains "وزارة العدل قديمة"
::   - reasoning_trace.known_unknowns contains 3 Qatar legality items
::     (تعديلات غير مرخصة / ملاحق غير موثقة / شهادة إتمام الإشغال)
::   - reasoning_trace.disclaimer ends "...FGRealty، PropertyFinder، arady)"

curl -s https://thammen.qa/api/disclaimer | findstr Mzad
:: expect: (no output — Mzad fully removed)

curl -s https://thammen.qa/api/about | findstr Mzad
:: expect: (no output — Mzad fully removed)
```

---

## Pre-deploy 6-item checklist (Project Instructions §5)

1. ✅ `py_compile` on `evaluate_unified.py`, `stock_strata.py`,
   `reasoning_trace.py`, `api.py` (no errors).
2. ⚠️ `node --check` on inline JS from `index.html` — NOT RUN locally
   (CC env). Anas to verify before push.
3. ⚠️ Mobile viewport 390×844 — NOT RUN. Anas to verify the trend
   card renders the new "اتجاه تاريخي" headline (and that the
   default `اتجاه السوق` headline still renders for fresh+low cases
   if any synthetic fixture is available).
4. ✅ Regression — 4 harnesses all green (see Tests above).
5. ✅ Isolated logic tests for new code — 39/39 PASS.
6. ⚠️ Smoke test 3 diverse addresses from Heroku post-deploy — to be
   run by Anas after push.

Items 2, 3, 6 are environment-bound and reserved for Anas.

---

*End of CHANGELOG_v54. Pre-existing Heroku v138 engine
`thammen-sprint2p16p17-security-hardening`; this Sprint replaces it
with `thammen-sprint2p22p0a3-arabic-surface-honesty` upon push.*

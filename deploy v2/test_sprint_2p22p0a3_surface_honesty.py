"""
test_sprint_2p22p0a3_surface_honesty.py
— Sprint 2.22.0a.3 (Arabic Surface Honesty Pass) isolated tests.

Covers (Sprint reopened after first push-block — gate was undersized):

  T1.1   Drop fabricated "بحالة جيدة" claim
  T1.2   STALENESS-COUPLED gate (corrected): suppress numeric trend
         slope_pct when MoJ data_freshness.tier in ('stale','very_stale')
         OR material_uncertainty.level in ('high','critical'). Self-
         healing — slope returns automatically when MoJ refreshes.
  T1.3   "تقييم كامل" → "تحليل آلي" at 3 user-visible sites
  T1.4   Named "10-Year-Rule" → observed-pattern phrasing at 3 sites
  T2.5   "±20-40%" → qualitative at 2 sites
  T2.7   Qatar legality gaps added to villa-path reasoning_trace
         (3 items — deduped from initial 4; subdivision covered by
         existing standard list's "حصص غير مفروزة")
  T-mzad Drop Mzad from 3 user-visible disclaimers + 1 sources array
         (Mzadqatar is T5 permanently excluded — listing it claimed
         a source we don't use)

Test discipline (Rule E14): substring checks against source files for
user-visible Arabic strings, AND functional checks that exercise the
actual production functions (add_standard_unknowns; synthetic
freshness_tier + muc_level for trend gating; ReasoningTrace
instantiation for disclaimer). Tests print a PASSED: X/Y summary
line for run_sprint_2p22p0a_suite.py aggregator parsing.

Standalone — no pytest dependency. Run as:

    PYTHONIOENCODING=utf-8 python test_sprint_2p22p0a3_surface_honesty.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent
sys.path.insert(0, str(REPO_ROOT))


# ──────────────────────────────────────────────────────────────────────
# Source-file helpers
# ──────────────────────────────────────────────────────────────────────

def _read(name: str) -> str:
    return (REPO_ROOT / name).read_text(encoding='utf-8')


_EU_SRC = _read('evaluate_unified.py')
_STRATA_SRC = _read('stock_strata.py')
_INDEX_SRC = _read('index.html')
_RT_SRC = _read('reasoning_trace.py')
_API_SRC = _read('api.py')


# ──────────────────────────────────────────────────────────────────────
# T1.1 — drop "بحالة جيدة" fabricated claim
# ──────────────────────────────────────────────────────────────────────

def test_t1_1_fabricated_condition_phrase_dropped():
    """The phrase 'لبناء بحالة جيدة' must not appear in the
    user-visible building decomposition interpretation."""
    forbidden = 'لبناء بحالة جيدة على هذه الأرض'
    assert forbidden not in _EU_SRC, (
        f"T1.1 regression: fabricated condition claim {forbidden!r} "
        f"still in evaluate_unified.py — the engine has no condition "
        f"ground truth and must not assert one."
    )
    print('  PASS test_t1_1_fabricated_condition_phrase_dropped')


def test_t1_1_normal_branch_still_narrates_pct():
    """The normal-status branch must still narrate the building share
    (the pct interpolation must remain — only the condition claim is
    dropped)."""
    assert 'ضمن النطاق النموذجي لمبنى على هذه الأرض' in _EU_SRC, (
        "T1.1 wiring: replacement phrase missing"
    )
    print('  PASS test_t1_1_normal_branch_still_narrates_pct')


# ──────────────────────────────────────────────────────────────────────
# T1.2 (REWORK) — staleness-coupled trend gate
# ──────────────────────────────────────────────────────────────────────
# Why the original 2.22.0a.3 gate was wrong: it suppressed only on
# MUC level in ('critical','high'), which never fires on the brief's
# named contradiction case (56/565/21 — moderate MUC + stale MoJ).
# With MoJ parked at 148-day staleness, every typical address sits at
# 'moderate' MUC (no field inspection) and the high/critical-only gate
# was a no-op in production.
#
# Corrected gate: suppress when data_freshness.tier in ('stale',
# 'very_stale') OR muc_level in ('high','critical'). Self-healing —
# slope returns when MoJ publishes fresh data, no code change needed.
#
# Tests parameterize BOTH freshness_tier and muc_level into a synthetic
# replay of the production gating block. The substring tests below
# additionally pin the production source to the corrected gate
# structure (so the synthetic test isn't checking dead code).

class _EvStub:
    """Minimal stub matching the attribute access pattern of the real
    PropertyEvaluation object at the trend-emission site."""
    def __init__(self, trend):
        self.trend = trend


def _run_trend_emission(freshness_tier, muc_level,
                        slope_annual_pct=0.0189, years=None):
    """Replay the production trend-emission block (evaluate_unified.py
    ~lines 4155-4225 post-T1.2-rework) against a synthetic output dict.

    Both gate inputs are parameters (no real MoJ CSV or MUC computation
    required). Replays the production logic verbatim — including the
    historical window construction and the suppression-reason field.

    Returns the populated `output['trend']` dict.

    NB: This mirrors production for deterministic testing. The two
    `test_t1_2_production_source_has_*` tests below verify the
    production source actually carries this logic.
    """
    if years is None:
        years = [
            {'year': 2020, 'n': 12}, {'year': 2021, 'n': 14},
            {'year': 2022, 'n': 11}, {'year': 2023, 'n': 13},
            {'year': 2024, 'n': 10}, {'year': 2025, 'n': 9},
        ]
    output = {}
    if muc_level is not None:
        output['material_uncertainty'] = {'level': muc_level}
    ev = _EvStub({
        'label': 'استقرار',
        'slope_annual_pct': slope_annual_pct,
        'years': years,
    })
    slope_pct = (ev.trend.get('slope_annual_pct') or 0) * 100
    yrs = ev.trend.get('years', [])
    annual_ns = [y.get('n', 0) for y in yrs]
    total_n = sum(annual_ns)
    min_year_n = min(annual_ns) if annual_ns else 0
    trend_supportable = (
        len(yrs) >= 2 and min_year_n >= 5 and total_n >= 10
    )
    if trend_supportable:
        _muc_level = (output.get('material_uncertainty') or {}).get('level')
        _fresh_tier = freshness_tier  # synthetic injection
        _suppress_slope = (
            _fresh_tier in ('stale', 'very_stale')
            or _muc_level in ('high', 'critical')
        )
        _year_nums = sorted({y.get('year') for y in yrs
                             if y.get('year') is not None})
        # Sprint 2.22.0a.3 LRM fix mirror: wrap year-range LTR run
        # with U+200E so the replay matches production output byte-
        # for-byte.
        _window_ar = (
            f'نافذة ‎{_year_nums[0]}–{_year_nums[-1]}‎'
            if _year_nums else 'نافذة غير محددة'
        )
        output['trend'] = {
            'label': ev.trend.get('label'),
            'years': yrs,
            'historical_window_ar': _window_ar,
        }
        if not _suppress_slope:
            output['trend']['slope_pct'] = round(slope_pct, 1)
            if abs(slope_pct) > 8:
                output['trend']['warning'] = (
                    f'⚠️ اتجاه استثنائي ({slope_pct:+.1f}%/سنة) — '
                    f'لا يُستخدم للاستقراء. النمو المستدام في قطر 2-4%/سنة.'
                )
        else:
            if _fresh_tier in ('stale', 'very_stale'):
                # Sprint 2.22.0a.3 LRM fix mirror: wrap the "91" digit
                # run with U+200E.
                output['trend']['suppressed_reason_ar'] = (
                    'بيانات وزارة العدل قديمة (≥ ‎91‎ يوماً) — '
                    'لا تدعم رقماً سنوياً دقيقاً اليوم.'
                )
            else:
                # No Latin/digit run in this branch — pure Arabic, no LRM.
                output['trend']['suppressed_reason_ar'] = (
                    'تحفظ مادي عند مستوى عالٍ/حرج — '
                    'العينة أو المنهجية قاصرة عن دعم رقم محدد.'
                )
    return output.get('trend')


def test_t1_2_slope_suppressed_when_stale():
    """ANCHOR CASE: today's production reality (148-day MoJ staleness
    → tier='stale'). With 'moderate' MUC (typical desktop call), slope
    MUST be suppressed. This is THE bug the reopened gate fixes — the
    original 2.22.0a.3 high/critical-only gate never fired here."""
    trend = _run_trend_emission(freshness_tier='stale', muc_level='moderate')
    assert 'slope_pct' not in trend, (
        f"T1.2 ANCHOR FAIL: slope_pct must be suppressed when MoJ "
        f"is stale (today's 148-day reality). Got: {trend!r}"
    )
    assert trend.get('label') == 'استقرار', (
        "T1.2: qualitative label must remain when slope is suppressed"
    )
    assert 'historical_window_ar' in trend, (
        "T1.2: historical_window_ar must be emitted on suppression"
    )
    assert trend['historical_window_ar'].startswith('نافذة '), (
        f"T1.2: window must start with 'نافذة', got {trend['historical_window_ar']!r}"
    )
    assert 'suppressed_reason_ar' in trend, (
        "T1.2: suppressed_reason_ar (transparency field) must be emitted"
    )
    assert 'وزارة العدل قديمة' in trend['suppressed_reason_ar'], (
        f"T1.2: staleness suppression reason must name the cause, "
        f"got {trend['suppressed_reason_ar']!r}"
    )
    assert 'warning' not in trend, (
        "T1.2: exceptional-slope warning must NOT appear when slope is suppressed"
    )
    print('  PASS test_t1_2_slope_suppressed_when_stale')


def test_t1_2_slope_suppressed_when_very_stale():
    """At 181+ days old, tier=very_stale → also suppress."""
    trend = _run_trend_emission(freshness_tier='very_stale',
                                muc_level='moderate')
    assert 'slope_pct' not in trend
    assert 'وزارة العدل قديمة' in trend['suppressed_reason_ar']
    print('  PASS test_t1_2_slope_suppressed_when_very_stale')


def test_t1_2_slope_suppressed_when_muc_critical_even_if_fresh():
    """When MoJ is fresh BUT MUC is critical (e.g. n=0 comparables),
    the methodology shortfall still warrants suppression."""
    trend = _run_trend_emission(freshness_tier='fresh', muc_level='critical')
    assert 'slope_pct' not in trend
    assert 'تحفظ مادي' in trend['suppressed_reason_ar']
    print('  PASS test_t1_2_slope_suppressed_when_muc_critical_even_if_fresh')


def test_t1_2_slope_suppressed_when_muc_high_even_if_fresh():
    trend = _run_trend_emission(freshness_tier='fresh', muc_level='high')
    assert 'slope_pct' not in trend
    print('  PASS test_t1_2_slope_suppressed_when_muc_high_even_if_fresh')


def test_t1_2_slope_retained_when_fresh_and_low():
    """The ONLY path where the numeric trend appears: MoJ fresh +
    low MUC. Rare today at 148-day staleness, but the gate must let
    it through when conditions improve (self-heal)."""
    trend = _run_trend_emission(freshness_tier='fresh', muc_level='low')
    assert 'slope_pct' in trend, (
        f"T1.2 self-heal: slope must appear when fresh+low. Got: {trend!r}"
    )
    assert trend['slope_pct'] == 1.9, (
        f"T1.2: rounding broken. Expected 1.9, got {trend['slope_pct']!r}"
    )
    # Window string is still emitted (it's part of the standard output now,
    # not gated on suppression)
    assert 'historical_window_ar' in trend, (
        "T1.2: historical_window_ar should also be present even when slope retained"
    )
    print('  PASS test_t1_2_slope_retained_when_fresh_and_low')


def test_t1_2_slope_retained_when_mild_and_low():
    """tier='mild' (31-90 days) is acceptable — the gate fires at
    'stale' (91+ days), not before."""
    trend = _run_trend_emission(freshness_tier='mild', muc_level='low')
    assert 'slope_pct' in trend, (
        "T1.2: 'mild' tier must not trigger suppression"
    )
    print('  PASS test_t1_2_slope_retained_when_mild_and_low')


def test_t1_2_slope_retained_when_fresh_and_moderate():
    """Fresh data + ambient 'moderate' MUC (desktop default) → retain.
    'moderate' is NOT a suppression trigger — only high/critical are.
    Proves the gate doesn't over-suppress on every desktop call once
    MoJ refreshes."""
    trend = _run_trend_emission(freshness_tier='fresh', muc_level='moderate')
    assert 'slope_pct' in trend, (
        "T1.2: ambient 'moderate' MUC must not block slope when MoJ is fresh"
    )
    print('  PASS test_t1_2_slope_retained_when_fresh_and_moderate')


def test_t1_2_slope_rounded_to_1_decimal_eliminates_float_noise():
    """Pre-rework, the value serialized as 1.8900000000000001 (float
    noise). Post-rework: exactly 1.9."""
    trend = _run_trend_emission(freshness_tier='fresh', muc_level='low',
                                 slope_annual_pct=0.0189)
    assert trend['slope_pct'] == 1.9
    serialized = json.dumps(trend['slope_pct'])
    assert serialized == '1.9', (
        f"T1.2: JSON serialization still carries float noise: {serialized!r}"
    )
    print('  PASS test_t1_2_slope_rounded_to_1_decimal_eliminates_float_noise')


def test_t1_2_historical_window_format():
    """The window string follows 'نافذة <LRM>YYYY–YYYY<LRM>' format
    with en-dash (U+2013) range separator, LRM-bracketed (U+200E) to
    prevent bidi reversal. Spans min/max years observed."""
    LRM = '‎'
    trend = _run_trend_emission(freshness_tier='stale', muc_level='low')
    assert 'historical_window_ar' in trend
    pattern = re.compile(r'^نافذة ‎\d{4}–\d{4}‎$')
    assert pattern.match(trend['historical_window_ar']), (
        f"T1.2: window must match 'نافذة <LRM>YYYY–YYYY<LRM>' format, got "
        f"{trend['historical_window_ar']!r}"
    )
    assert trend['historical_window_ar'] == f'نافذة {LRM}2020–2025{LRM}', (
        f"T1.2: expected default-fixture window "
        f"'نافذة {LRM}2020–2025{LRM}', got {trend['historical_window_ar']!r}"
    )
    print('  PASS test_t1_2_historical_window_format')


def test_t1_2_production_source_has_staleness_coupled_gate():
    """Substring sanity: the production source carries the CORRECTED
    gate (NOT the original undersized high/critical-only form)."""
    # The original wrong form MUST NOT appear
    assert "_muc_suppresses_slope = _muc_level in ('critical', 'high')" \
        not in _EU_SRC, (
        "T1.2 REGRESSION: the original undersized gate "
        "(`_muc_suppresses_slope = level in critical/high`) is still "
        "in the production source. The rework was meant to replace it."
    )
    # The corrected form MUST be present
    assert "_fresh_tier = _get_moj_freshness_tier()" in _EU_SRC, (
        "T1.2: freshness lookup at the gate site missing"
    )
    assert "_fresh_tier in ('stale', 'very_stale')" in _EU_SRC, (
        "T1.2: staleness branch of the OR-gate missing"
    )
    assert "_muc_level in ('high', 'critical')" in _EU_SRC, (
        "T1.2: MUC branch of the OR-gate missing"
    )
    assert "_suppress_slope = (" in _EU_SRC, (
        "T1.2: corrected suppression variable name missing"
    )
    print('  PASS test_t1_2_production_source_has_staleness_coupled_gate')


def test_t1_2_production_source_has_freshness_helper():
    """The freshness cache helper exists and uses lazy import to avoid
    circular dependency with api.py."""
    assert "def _get_moj_freshness_tier" in _EU_SRC, (
        "T1.2: _get_moj_freshness_tier helper missing"
    )
    assert "from data_freshness import compute_freshness" in _EU_SRC, (
        "T1.2: lazy import of compute_freshness missing"
    )
    assert "_ENGINE_FRESHNESS_CACHE" in _EU_SRC, (
        "T1.2: module-level freshness cache missing"
    )
    print('  PASS test_t1_2_production_source_has_freshness_helper')


def test_t1_2_production_source_emits_window_and_reason():
    """Production emits historical_window_ar always (when supportable)
    and suppressed_reason_ar when the gate fires."""
    assert "'historical_window_ar'" in _EU_SRC, (
        "T1.2: production must emit historical_window_ar"
    )
    assert "'suppressed_reason_ar'" in _EU_SRC, (
        "T1.2: production must emit suppressed_reason_ar on suppression"
    )
    print('  PASS test_t1_2_production_source_emits_window_and_reason')


def test_t1_2_frontend_renders_historical_framing_when_slope_absent():
    """The index.html trend card now reframes the headline to 'اتجاه
    تاريخي' + historical window when backend suppresses slope_pct.
    When slope is present, the original 'اتجاه السوق' framing remains."""
    # Suppressed-path headline
    assert "trHeadline='اتجاه تاريخي: '" in _INDEX_SRC, (
        "T1.2 frontend: suppressed-path 'اتجاه تاريخي' headline missing"
    )
    assert "tr.historical_window_ar" in _INDEX_SRC, (
        "T1.2 frontend: historical_window_ar reference missing"
    )
    # Original headline preserved for the slope-present path
    assert "اتجاه السوق:" in _INDEX_SRC, (
        "T1.2 frontend: 'اتجاه السوق' headline (slope-present path) lost"
    )
    print('  PASS test_t1_2_frontend_renders_historical_framing_when_slope_absent')


# T1.2 LRM bidi-wrap sentinels (Sprint 2.22.0a.3 pre-push fix)
# ──────────────────────────────────────────────────────────────────────
# The new T1.2 strings embed LTR runs (digit year-ranges, the "91"
# day-count) inside Arabic text. Without U+200E (LRM) bracketing,
# under `dir="rtl"` the runs can visually reverse — same bidi class
# as the historic "31/918/99 → 99/918/31" reversal documented in
# Operational_Rules #25. The convention mirrors muc_clause_ar where
# "‎VPGA 10‎", "‎IVS 106‎", "‎effective 31 January 2025‎" are wrapped.
# These sentinels catch future regressions that re-introduce
# unwrapped digit runs into Arabic copy.

def test_t1_2_historical_window_lrm_wrapped():
    """The year-range LTR run in historical_window_ar must be
    bracketed by U+200E on both sides."""
    LRM = '‎'  # U+200E
    trend = _run_trend_emission(freshness_tier='stale', muc_level='moderate')
    win = trend['historical_window_ar']
    # The full year-range plus its dash must be wrapped
    assert f'{LRM}2020–2025{LRM}' in win, (
        f"T1.2 LRM regression: year-range not LRM-wrapped. Got: {win!r}"
    )
    # Sanity: exactly 2 LRM markers (open + close)
    assert win.count(LRM) == 2, (
        f"T1.2 LRM: expected exactly 2 U+200E markers in window, got "
        f"{win.count(LRM)}. Got: {win!r}"
    )
    print('  PASS test_t1_2_historical_window_lrm_wrapped')


def test_t1_2_suppressed_reason_staleness_lrm_wrapped():
    """The '91' digit run in the staleness suppression reason must
    be bracketed by U+200E. The surrounding '≥ ' (math symbol +
    space) and ' يوماً' (Arabic) stay outside the wrap, matching
    the muc_clause_ar 'wrap LTR runs only' convention."""
    LRM = '‎'
    trend = _run_trend_emission(freshness_tier='stale', muc_level='moderate')
    reason = trend['suppressed_reason_ar']
    assert f'≥ {LRM}91{LRM} يوماً' in reason, (
        f"T1.2 LRM regression: '91' digit run not bracketed by U+200E "
        f"in staleness reason. Got: {reason!r}"
    )
    print('  PASS test_t1_2_suppressed_reason_staleness_lrm_wrapped')


def test_t1_2_suppressed_reason_muc_branch_pure_arabic_no_lrm():
    """Defensive: the MUC-level suppression branch text is pure
    Arabic (uses 'عالٍ/حرج', not Latin level names). No LRM should
    be inserted — over-wrapping pure-Arabic strings is a different
    bidi anti-pattern."""
    trend = _run_trend_emission(freshness_tier='fresh', muc_level='critical')
    reason = trend['suppressed_reason_ar']
    assert '‎' not in reason, (
        f"T1.2 LRM over-wrap: MUC-branch reason is pure Arabic — "
        f"U+200E must not appear. Got: {reason!r}"
    )
    print('  PASS test_t1_2_suppressed_reason_muc_branch_pure_arabic_no_lrm')


def test_oos_detector_regex_includes_en_dash():
    """Operational_Rules #25 detector regex must include EN-DASH
    (U+2013) in its separator class — without it, year-range tokens
    like '2020–2025' would not trigger the LRM-wrap heuristic
    (would only catch hyphen-minus '2025-12-31'-style tokens)."""
    rules_text = (REPO_ROOT / 'docs' / 'Operational_Rules.md').read_text(
        encoding='utf-8'
    )
    # Find the detector line containing the separator class
    # Looking for: /[\/.,:°²×\-–]/ (the en-dash addition)
    assert '°²×\\-–' in rules_text, (
        "Operational_Rules #25: separator class must include EN-DASH "
        "(U+2013) — Sprint 2.22.0a.3 LRM-rework added it for "
        "year-range tokens. Detector regex looks stale."
    )
    print('  PASS test_oos_detector_regex_includes_en_dash')


# ──────────────────────────────────────────────────────────────────────
# T1.3 — تقييم كامل → تحليل آلي (3 sites)
# ──────────────────────────────────────────────────────────────────────

def test_t1_3_old_phrase_absent_from_evaluate_unified():
    forbidden_1 = "للحصول على تقييم كامل"
    forbidden_2 = "لتقييم كامل يرجى تزويدنا"
    assert forbidden_1 not in _EU_SRC, f"T1.3 regression: {forbidden_1!r}"
    assert forbidden_2 not in _EU_SRC, f"T1.3 regression: {forbidden_2!r}"
    print('  PASS test_t1_3_old_phrase_absent_from_evaluate_unified')


def test_t1_3_old_phrase_absent_from_index_html():
    forbidden = "scopeLabel='تقييم كامل'"
    assert forbidden not in _INDEX_SRC, f"T1.3 regression: {forbidden!r}"
    print('  PASS test_t1_3_old_phrase_absent_from_index_html')


def test_t1_3_new_phrase_present_at_3_sites():
    assert "للحصول على تحليل آلي" in _EU_SRC
    assert "لتحليل آلي يرجى تزويدنا" in _EU_SRC
    assert "scopeLabel='تحليل آلي'" in _INDEX_SRC
    print('  PASS test_t1_3_new_phrase_present_at_3_sites')


# ──────────────────────────────────────────────────────────────────────
# T1.4 — Named "10-Year-Rule" → observation
# ──────────────────────────────────────────────────────────────────────

def test_t1_4_named_rule_absent_from_user_visible_sites():
    forbidden_interp = "يتسق مع قاعدة الـ 10 سنوات: السوق القطري"
    assert forbidden_interp not in _EU_SRC
    forbidden_label = "regime_label_ar = 'قاعدة الـ 10 سنوات (السوق القطري)'"
    assert forbidden_label not in _EU_SRC
    forbidden_strata = "تنطبق عليها قاعدة الـ10-Year-Rule"
    assert forbidden_strata not in _STRATA_SRC
    print('  PASS test_t1_4_named_rule_absent_from_user_visible_sites')


def test_t1_4_tendency_phrasing_present():
    """Post-validation fold (Rule #54): GPT+Gemini both flagged the
    prior 'كعبء معماري' framing. Replaced with TENDENCY prose at
    the long-form interp site, and a short DESCRIPTIVE TAG at the
    regime-label + stratum-description sites."""
    # Long-form prose (interp at eu.py). Source uses implicit Python
    # string concat across lines, so check distinctive sub-substrings
    # that fit on a single source line rather than the full sentence.
    assert 'غالباً ما تتراجع مساهمة البناء في القيمة مع تقادم العقار' in _EU_SRC, (
        "T1.4 prose (interp): tendency-opening clause missing"
    )
    assert 'السكني دون تجديد، فتصبح الأرض المكوّن الأكبر في التسعير' in _EU_SRC, (
        "T1.4 prose (interp): tendency-closer clause missing"
    )
    # Short descriptive tag at the regime-label site
    assert "regime_label_ar = 'نمط سوقي: غلبة قيمة الأرض في العقارات القديمة'" in _EU_SRC, (
        "T1.4 short tag (regime_label_ar) missing"
    )
    # Short descriptive tag at the stratum-description site
    assert "'نمط سوقي: غلبة قيمة الأرض في العقارات القديمة'" in _STRATA_SRC, (
        "T1.4 short tag (STRATUM_DESC_AR['land_priced']) missing"
    )
    print('  PASS test_t1_4_tendency_phrasing_present')


def test_t1_4_provocative_burden_phrasing_GONE():
    """Post-validation fold: 'كعبء معماري' was flagged by both AIs
    (GPT: provocative; Gemini: implies universality). Must be absent
    from every user-visible site."""
    assert 'كعبء معماري' not in _EU_SRC, (
        "T1.4 regression: 'كعبء معماري' still in evaluate_unified.py"
    )
    assert 'كعبء معماري' not in _STRATA_SRC, (
        "T1.4 regression: 'كعبء معماري' still in stock_strata.py"
    )
    # Also confirm the prior interp-phrasing's flat-rule form is gone
    assert 'نمط ملاحظ في الفئات القديمة بالسوق القطري' not in _EU_SRC, (
        "T1.4 regression: prior pre-fold interp phrasing still in source"
    )
    assert 'نمط الفئات القديمة (تقارب سعر التداول من قيمة الأرض)' not in _EU_SRC, (
        "T1.4 regression: prior pre-fold regime label still in source"
    )
    print('  PASS test_t1_4_provocative_burden_phrasing_GONE')


def test_t1_4_disclosure_function_softening_preserved():
    """Sprint 2.22.0a.2 §9 softening MUST NOT be disturbed."""
    assert "بناءً على {n} صفقة قريبة في النوع والمساحة من نفس المنطقة" in _EU_SRC
    print('  PASS test_t1_4_disclosure_function_softening_preserved')


def test_t1_4_internal_regime_constant_preserved():
    """Internal dispatch constant stays — user-visible copy only changed."""
    assert "'qatar_10_year_rule'" in _EU_SRC
    print('  PASS test_t1_4_internal_regime_constant_preserved')


# ──────────────────────────────────────────────────────────────────────
# T2.5 — ±20-40% → qualitative
# ──────────────────────────────────────────────────────────────────────

def test_t2_5_quantitative_range_absent_from_backend():
    forbidden = 'وقد يختلف عن الواقع بـ ±20-40%'
    assert forbidden not in _EU_SRC
    print('  PASS test_t2_5_quantitative_range_absent_from_backend')


def test_t2_5_quantitative_range_absent_from_frontend():
    forbidden = 'الفرق قد يكون ±20-40%'
    assert forbidden not in _INDEX_SRC
    print('  PASS test_t2_5_quantitative_range_absent_from_frontend')


def test_t2_5_causal_phrase_present_in_backend():
    """Post-validation fold (Rule #54): GPT pushed back on the vague
    'بشكل ملحوظ' wording — replaced with causal+specific framing
    that names the inputs which would move the estimate. Pairs with
    T1.1: T1.1 dropped the unsupported condition claim; T2.5 here
    names condition as exactly what would refine the estimate."""
    assert (
        'قد يؤدي إدخال التفاصيل الفعلية للعقار'
    ) in _EU_SRC, "T2.5 backend: causal framing opening missing"
    assert 'كالحالة والمساحة الدقيقة والتشطيبات' in _EU_SRC, (
        "T2.5 backend: causal inputs (condition/area/finishes) missing"
    )
    assert 'إلى تعديل جوهري في التقدير' in _EU_SRC, (
        "T2.5 backend: causal closer missing"
    )
    print('  PASS test_t2_5_causal_phrase_present_in_backend')


def test_t2_5_causal_phrase_present_in_frontend():
    """Same causal+specific wording at the frontend disclaimer card."""
    assert (
        'قد يؤدي إدخال التفاصيل الفعلية للعقار'
    ) in _INDEX_SRC, "T2.5 frontend: causal framing opening missing"
    assert 'كالحالة والمساحة الدقيقة والتشطيبات' in _INDEX_SRC, (
        "T2.5 frontend: causal inputs missing"
    )
    assert 'إلى تعديل جوهري في التقدير' in _INDEX_SRC, (
        "T2.5 frontend: causal closer missing"
    )
    print('  PASS test_t2_5_causal_phrase_present_in_frontend')


def test_t2_5_prior_vague_phrasing_GONE():
    """Post-validation fold: the prior pre-fold qualitative phrasings
    (vague 'بشكل ملحوظ' / 'الفرق قد يكون ملحوظاً') were flagged by
    GPT as inadequate replacements for a fake-precise range. Must
    be absent from both sites."""
    assert 'يختلف عن الواقع بشكل ملحوظ' not in _EU_SRC, (
        "T2.5 regression (backend): prior vague phrasing still in source"
    )
    assert 'الفرق قد يكون ملحوظاً' not in _INDEX_SRC, (
        "T2.5 regression (frontend): prior vague phrasing still in source"
    )
    print('  PASS test_t2_5_prior_vague_phrasing_GONE')


# ──────────────────────────────────────────────────────────────────────
# T2.7 (deduped) — 3 Qatar legality gaps in villa-path
# ──────────────────────────────────────────────────────────────────────
# Original Sprint 2.22.0a.3 first pass added 4 items, including
# subdivision/parcellation. Subdivision is already covered by the
# standard list ("أي التزامات قانونية ... حصص غير مفروزة"), so the
# rework drops it. Item 3 reworked to OCCERT (occupancy completion
# certificate) per Anas — a distinct verification path the engine
# cannot cover from GIS/MoJ alone.

from reasoning_trace import (  # noqa: E402
    ReasoningTrace, add_standard_unknowns,
)

_LEGALITY_TOKENS_3 = [
    'تعديلات غير مرخصة',          # unauthorized modifications
    'ملاحق وإضافات غير موثقة',     # undocumented extensions
    'شهادة إتمام الإشغال',         # OCCERT verification
]

# This token used to appear in the first pass — must be absent after dedup
_DROPPED_LEGALITY_TOKEN = 'وضع التقسيم والفرز الرسمي'


def test_t2_7_three_legality_items_in_villa_standalone():
    """3 items (not 4). Subdivision check dropped — it's already
    covered by the standard list's 'حصص غير مفروزة' line."""
    trace = ReasoningTrace()
    add_standard_unknowns(trace, asset_type='villa_standalone')
    joined = '\n'.join(trace.known_unknowns)
    for tok in _LEGALITY_TOKENS_3:
        assert tok in joined, (
            f"T2.7: legality token {tok!r} missing from villa_standalone "
            f"known_unknowns. Got: {trace.known_unknowns}"
        )
    print('  PASS test_t2_7_three_legality_items_in_villa_standalone')


def test_t2_7_three_legality_items_in_villa_compound():
    trace = ReasoningTrace()
    add_standard_unknowns(trace, asset_type='villa_compound')
    joined = '\n'.join(trace.known_unknowns)
    for tok in _LEGALITY_TOKENS_3:
        assert tok in joined
    print('  PASS test_t2_7_three_legality_items_in_villa_compound')


def test_t2_7_subdivision_NOT_re_added_as_separate_item():
    """Dedup contract: the standalone 'وضع التقسيم والفرز الرسمي'
    item must NOT appear — subdivision is covered by the standard
    list's 'حصص غير مفروزة' phrase."""
    trace = ReasoningTrace()
    add_standard_unknowns(trace, asset_type='villa_standalone')
    joined = '\n'.join(trace.known_unknowns)
    assert _DROPPED_LEGALITY_TOKEN not in joined, (
        f"T2.7 DEDUP REGRESSION: dropped item {_DROPPED_LEGALITY_TOKEN!r} "
        f"was re-added. Subdivision is covered by 'حصص غير مفروزة' in "
        f"the standard list."
    )
    print('  PASS test_t2_7_subdivision_NOT_re_added_as_separate_item')


def test_t2_7_subdivision_covered_by_standard_list():
    """Confirm the standard-list coverage that justifies the dedup."""
    trace = ReasoningTrace()
    add_standard_unknowns(trace, asset_type='villa_standalone')
    joined = '\n'.join(trace.known_unknowns)
    assert 'حصص غير مفروزة' in joined, (
        "T2.7 dedup invariant: subdivision concept must remain "
        "covered by the standard list's 'حصص غير مفروزة' phrase"
    )
    print('  PASS test_t2_7_subdivision_covered_by_standard_list')


def test_t2_7_legality_items_NOT_in_apartment():
    """Apartments don't get the villa-specific legality block."""
    trace = ReasoningTrace()
    add_standard_unknowns(trace, asset_type='apartment')
    joined = '\n'.join(trace.known_unknowns)
    for tok in _LEGALITY_TOKENS_3:
        assert tok not in joined, (
            f"T2.7 over-reach: villa-only token {tok!r} leaked into "
            f"apartment. Got: {trace.known_unknowns}"
        )
    print('  PASS test_t2_7_legality_items_NOT_in_apartment')


def test_t2_7_pre_existing_villa_items_preserved():
    """The pre-existing villa-specific items (garden/pool, walls/roof)
    must still be present — T2.7 is additive, not replacement."""
    trace = ReasoningTrace()
    add_standard_unknowns(trace, asset_type='villa_standalone')
    joined = '\n'.join(trace.known_unknowns)
    assert 'الحديقة وحوض السباحة' in joined
    assert 'الجدران الخارجية والسقف' in joined
    print('  PASS test_t2_7_pre_existing_villa_items_preserved')


def test_t2_7_standard_universal_items_preserved():
    """The 4 standard items (all asset types) still present in villa output."""
    trace = ReasoningTrace()
    add_standard_unknowns(trace, asset_type='villa_standalone')
    joined = '\n'.join(trace.known_unknowns)
    assert 'حالة العقار الداخلية الفعلية' in joined
    assert 'أي التزامات قانونية' in joined
    assert 'تاريخ آخر تجديد فعلي' in joined
    assert 'وضع المستأجر الحالي' in joined
    print('  PASS test_t2_7_standard_universal_items_preserved')


# ──────────────────────────────────────────────────────────────────────
# T-mzad — drop Mzadqatar from user-visible source lists
# ──────────────────────────────────────────────────────────────────────
# Mzadqatar is permanently excluded from Thammen's data pipeline (T5
# auction-only source). Listing it in the user-visible disclaimers
# was a live honesty bug — it claimed a source we do not use.

def test_mzad_dropped_from_reasoning_trace_disclaimer():
    """reasoning_trace.ReasoningTrace.disclaimer default must not list Mzad."""
    rt = ReasoningTrace()
    assert 'Mzad' not in rt.disclaimer, (
        f"T-mzad: Mzad still in reasoning_trace.disclaimer: "
        f"{rt.disclaimer!r}"
    )
    # Confirm the parenthetical ends at arady)
    assert 'arady)' in rt.disclaimer, (
        "T-mzad: expected arady to be last source before closing paren"
    )
    print('  PASS test_mzad_dropped_from_reasoning_trace_disclaimer')


def test_mzad_dropped_from_api_disclaimer_ar():
    """api.py /api/disclaimer endpoint's disclaimer_ar must not list Mzad."""
    # Extract the Arabic disclaimer block specifically (between
    # `"disclaimer_ar":` and `"disclaimer_en":`)
    chunks = _API_SRC.split('"disclaimer_ar":')
    assert len(chunks) >= 2, "T-mzad: disclaimer_ar field not found in api.py"
    ar_block = chunks[1].split('"disclaimer_en":')[0]
    assert 'Mzad' not in ar_block, (
        f"T-mzad: Mzad still in api.py disclaimer_ar block"
    )
    print('  PASS test_mzad_dropped_from_api_disclaimer_ar')


def test_mzad_dropped_from_api_disclaimer_en():
    """api.py /api/disclaimer endpoint's disclaimer_en must not list Mzad."""
    # The English disclaimer specifically — look for the listings parenthetical
    assert 'PropertyFinder, arady)' in _API_SRC, (
        "T-mzad: expected English listings parenthetical to end at 'arady).'"
    )
    assert '(FGRealty, PropertyFinder, arady, Mzad)' not in _API_SRC, (
        "T-mzad: English disclaimer still lists Mzad"
    )
    print('  PASS test_mzad_dropped_from_api_disclaimer_en')


def test_mzad_dropped_from_api_sources_used_array():
    """api.py /api/about endpoint's data_sources.listings array must
    not include the Mzad Qatar entry."""
    assert '"Mzad Qatar"' not in _API_SRC, (
        "T-mzad: 'Mzad Qatar' entry still in api.py sources array"
    )
    assert 'mzadqatar.com' not in _API_SRC, (
        "T-mzad: mzadqatar.com URL still in api.py"
    )
    # Sanity: the other listings sources are still there
    assert '"FGRealty"' in _API_SRC
    assert '"PropertyFinder Qatar"' in _API_SRC
    assert '"arady.qa"' in _API_SRC
    print('  PASS test_mzad_dropped_from_api_sources_used_array')


# ──────────────────────────────────────────────────────────────────────
# Out-of-scope regression guards
# ──────────────────────────────────────────────────────────────────────

def test_oos_t2_6_shawahid_taxonomy_untouched():
    """T2.6 (dropped) — Sprint 2.22.0a.2 C3 taxonomy must not be
    accidentally modified."""
    assert 'شواهد كافية' in _EU_SRC
    print('  PASS test_oos_t2_6_shawahid_taxonomy_untouched')


def test_oos_c4_disclaimer_wording_preserved():
    """T2.8 (deferred) — the Sprint 2.22.0a.2 Pattern C4 disclaimer
    wording must remain verbatim at all 5 short-form sites in
    evaluate_unified.py."""
    c4_phrase = 'ولا يُعتبر تقرير تثمين رسمي صادر عن مثمّن مرخّص وفق معايير RICS/IVS'
    count = _EU_SRC.count(c4_phrase)
    assert count >= 5, (
        f"T2.8/C4 protection: expected ≥5 occurrences of C4 phrase "
        f"in evaluate_unified.py, got {count}"
    )
    print(f'  PASS test_oos_c4_disclaimer_wording_preserved (count={count})')


# ──────────────────────────────────────────────────────────────────────
# Runner
# ──────────────────────────────────────────────────────────────────────

ALL_TESTS = [
    # T1.1
    test_t1_1_fabricated_condition_phrase_dropped,
    test_t1_1_normal_branch_still_narrates_pct,
    # T1.2 (REWORK)
    test_t1_2_slope_suppressed_when_stale,
    test_t1_2_slope_suppressed_when_very_stale,
    test_t1_2_slope_suppressed_when_muc_critical_even_if_fresh,
    test_t1_2_slope_suppressed_when_muc_high_even_if_fresh,
    test_t1_2_slope_retained_when_fresh_and_low,
    test_t1_2_slope_retained_when_mild_and_low,
    test_t1_2_slope_retained_when_fresh_and_moderate,
    test_t1_2_slope_rounded_to_1_decimal_eliminates_float_noise,
    test_t1_2_historical_window_format,
    test_t1_2_production_source_has_staleness_coupled_gate,
    test_t1_2_production_source_has_freshness_helper,
    test_t1_2_production_source_emits_window_and_reason,
    test_t1_2_frontend_renders_historical_framing_when_slope_absent,
    # T1.2 LRM sentinels (pre-push fix)
    test_t1_2_historical_window_lrm_wrapped,
    test_t1_2_suppressed_reason_staleness_lrm_wrapped,
    test_t1_2_suppressed_reason_muc_branch_pure_arabic_no_lrm,
    test_oos_detector_regex_includes_en_dash,
    # T1.3
    test_t1_3_old_phrase_absent_from_evaluate_unified,
    test_t1_3_old_phrase_absent_from_index_html,
    test_t1_3_new_phrase_present_at_3_sites,
    # T1.4
    test_t1_4_named_rule_absent_from_user_visible_sites,
    test_t1_4_tendency_phrasing_present,
    test_t1_4_provocative_burden_phrasing_GONE,
    test_t1_4_disclosure_function_softening_preserved,
    test_t1_4_internal_regime_constant_preserved,
    # T2.5
    test_t2_5_quantitative_range_absent_from_backend,
    test_t2_5_quantitative_range_absent_from_frontend,
    test_t2_5_causal_phrase_present_in_backend,
    test_t2_5_causal_phrase_present_in_frontend,
    test_t2_5_prior_vague_phrasing_GONE,
    # T2.7 (deduped 4 → 3)
    test_t2_7_three_legality_items_in_villa_standalone,
    test_t2_7_three_legality_items_in_villa_compound,
    test_t2_7_subdivision_NOT_re_added_as_separate_item,
    test_t2_7_subdivision_covered_by_standard_list,
    test_t2_7_legality_items_NOT_in_apartment,
    test_t2_7_pre_existing_villa_items_preserved,
    test_t2_7_standard_universal_items_preserved,
    # T-mzad
    test_mzad_dropped_from_reasoning_trace_disclaimer,
    test_mzad_dropped_from_api_disclaimer_ar,
    test_mzad_dropped_from_api_disclaimer_en,
    test_mzad_dropped_from_api_sources_used_array,
    # Out-of-scope regression guards
    test_oos_t2_6_shawahid_taxonomy_untouched,
    test_oos_c4_disclaimer_wording_preserved,
]


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

    print('=' * 70)
    print('Sprint 2.22.0a.3 — Arabic Surface Honesty Pass (REWORKED)')
    print(f'Total tests: {len(ALL_TESTS)}')
    print('=' * 70)

    passed = 0
    failed = []
    for t in ALL_TESTS:
        try:
            t()
            passed += 1
        except AssertionError as e:
            failed.append((t.__name__, str(e)))
            print(f'  FAIL {t.__name__}: {e}')
        except Exception as e:
            failed.append((t.__name__, f'{type(e).__name__}: {e}'))
            print(f'  ERROR {t.__name__}: {type(e).__name__}: {e}')

    total = len(ALL_TESTS)
    print('=' * 70)
    print(f'PASSED: {passed}/{total}')
    print('=' * 70)

    if failed:
        print()
        print('Failures:')
        for name, msg in failed:
            print(f'  - {name}: {msg}')
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())

#!/usr/bin/env python3
"""
stock_strata.py — Sprint 2.16.0
═════════════════════════════════════════════════════════════════════════════
Per-stratum villa transaction classification per EMPIRICAL_FINDINGS Rule E4.

Background
──────────
Thammen's pre-2.16 villa valuation used a single bracket median (e.g. "Bou
Hamour 400-600 m², n=29, median 2.5M"). This is the empirically-confirmed
source of systematic under-valuation on modern/luxury stock — the bracket
mixes aging stock + modern + luxury into one number, dominated by the most-
frequent class (aging).

Probe results (2026-05-17, against thammen.qa production):

    PIN 56099695 (J Seven Bou Hamour A)     thammen 2,500,000 vs sale 4,000,000   −37.5%
    PIN 56099696 (J Seven Bou Hamour B)     thammen 2,400,000 vs sale 4,000,000   −40.0%
    PIN 51708152 (Al-Gharafa modern villa)  thammen 3,100,000 vs sale 4,450,000   −30.3%

Stratification (this module) brings Al-Gharafa to within +2.9% of the actual
sale price. J Seven remains under-valued (stratum data thin in that area)
but is correctly flagged as "above luxury_new band" rather than presented as
a confident point estimate.

Classification rule
───────────────────
For each MoJ villa transaction in an area:

    ratio = villa.price_per_m2 / land_median_per_m2_same_area

    ratio < 1.15       → land_priced   (Qatar 10-year rule territory)
    1.15 ≤ ratio < 1.50 → aging_stock  (mature buildings, common resale)
    1.50 ≤ ratio < 2.20 → modern_stock (newer, well-maintained, ready-to-move)
    ratio ≥ 2.20       → luxury_new    (luxury / brand-new construction)

Thresholds source: EMPIRICAL_FINDINGS 2026-05-13, paired audit of 5 areas
× 4 brackets, n=149+ MoJ + n=18 asking.

Empirical validation on 3 confirmed sales (2026-05-17):
  Al-Gharafa 51708152: ratio 1.89 → modern_stock; stratum median × plot
    = 4,576,800 vs sale 4,450,000 → error +2.9% (from −30.3%)
  J Seven A/B:         ratio 2.29 → luxury_new boundary; stratum n=1 in
    Bou Hamour (thin); subject correctly flagged as out-of-distribution.

Public API
──────────
    build_stock_strata_result(moj_rows, moj_area_names, villa_transactions,
                              plot_area_m2, listing_price, date_col)
        → dict ready for inclusion in /api/evaluate/details response,
          or None if data is insufficient.

Sprint scope (2.16.0)
─────────────────────
EXPOSURE ONLY. The headline `valuation.amount` is NOT changed by this Sprint.
Strata are surfaced as an additional field for user transparency. Future
sprints (2.17+) may allow user inputs to drive headline value to the
appropriate stratum.
"""

from __future__ import annotations

import re
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set


# ════════════════════════════════════════════════════════════════════════
# Sprint 2.16.0 — Stock Stratification (EMPIRICAL_FINDINGS Rule E4)
# ════════════════════════════════════════════════════════════════════════
STRATA_VERSION = '2.16.0'
RULE_SOURCE = 'EMPIRICAL_FINDINGS Rule E4 (2026-05-13)'

# (name, lo_inclusive, hi_exclusive)
STRATUM_THRESHOLDS = [
    ('land_priced',  None, 1.15),
    ('aging_stock',  1.15, 1.50),
    ('modern_stock', 1.50, 2.20),
    ('luxury_new',   2.20, None),
]

STRATUM_LABELS_AR = {
    'land_priced':  'بسعر الأرض',
    'aging_stock':  'بناء متوسط العمر',
    'modern_stock': 'بناء حديث جيد',
    'luxury_new':   'فاخر / حديث البناء',
}

STRATUM_DESC_AR = {
    'land_priced':
        # Sprint 2.22.0a.2 Pattern C2 mechanical drop: removed
        # "(Project Instructions §3)" internal-doc reference. The
        # methodology is documented in the user-facing reasoning trace
        # and does not require an internal-doc citation in the user copy.
        'فلل قديمة جداً تُباع بسعر الأرض تقريباً. تنطبق عليها قاعدة الـ10-Year-Rule '
        'في قطر: البناء عبء معماري، ليس قيمة مضافة.',
    'aging_stock':
        'فلل عمرها 10+ سنوات بتشطيب متوسط أو تجديد جزئي. '
        'الفئة الأكثر تكراراً في معظم مناطق قطر، وتميل إلى أن تكون مهيمنة على median المدمج.',
    'modern_stock':
        'فلل عمرها 2-10 سنوات، تشطيب جيد، حالة جاهزة للسكن بدون ترميم. '
        'كثيراً ما تكون قيمتها الحقيقية أعلى من median المدمج بنسبة 20-40%.',
    'luxury_new':
        'فلل جديدة (1-3 سنوات) مع تشطيب فاخر، أو مشاريع طور التطوير. '
        'في بعض المناطق تكون عينة هذه الفئة ضعيفة (n<5) فلا يُعتمد على median لها مباشرة.',
}

# Below this n, the stratum median is shown but flagged as indicative
RELIABLE_N = 10
MINIMUM_N_FOR_MEDIAN = 3

# Window for land median computation
DEFAULT_LAND_WINDOW_MONTHS = 24
FALLBACK_LAND_WINDOW_MONTHS = 36


# ────────────────────────────────────────────────────────────────────────
# Internal helpers
# ────────────────────────────────────────────────────────────────────────
def _norm(s) -> str:
    """Normalize whitespace, strip NBSP. Required for MoJ data."""
    return re.sub(r'\s+', ' ', s or '').strip()


def _to_float(s) -> Optional[float]:
    try:
        return float(str(s).replace(',', '').strip())
    except (ValueError, TypeError):
        return None


def _parse_date(s) -> Optional[datetime]:
    try:
        return datetime.strptime(_norm(s), '%Y-%m-%d')
    except (ValueError, TypeError):
        return None


def _is_land(type_ar) -> bool:
    """Match Arabic property type string against land categories."""
    t = _norm(type_ar)
    return t.startswith('أرض') or t.startswith('ارض')


def _median(xs):
    return statistics.median(xs) if xs else None


# ────────────────────────────────────────────────────────────────────────
# Public — classification primitives
# ────────────────────────────────────────────────────────────────────────
def classify_ratio(ratio: Optional[float]) -> str:
    """Classify a villa/land ratio into a stratum name."""
    if ratio is None or ratio <= 0:
        return 'unknown'
    for name, lo, hi in STRATUM_THRESHOLDS:
        if lo is None and ratio < hi:
            return name
        if hi is None and ratio >= lo:
            return name
        if lo is not None and hi is not None and lo <= ratio < hi:
            return name
    return 'unknown'


def _stratum_band_label(name: str) -> str:
    for n, lo, hi in STRATUM_THRESHOLDS:
        if n == name:
            if lo is None:
                return f'<{hi}'
            if hi is None:
                return f'≥{lo}'
            return f'{lo}-{hi}'
    return ''


# ────────────────────────────────────────────────────────────────────────
# Public — main computation
# ────────────────────────────────────────────────────────────────────────
def _bracket_for_plot(plot_area_m2: Optional[float]) -> Optional[tuple]:
    """Map a plot area to the standard size bracket (Project Instructions §3).

    Returns (lo, hi) where lo inclusive, hi exclusive. Bracket-match policy
    follows EMPIRICAL_FINDINGS Rule E4: land reference should align with
    villa plot size economics. Smaller plots have higher per-m² land prices.
    """
    if not plot_area_m2 or plot_area_m2 <= 0:
        return None
    if plot_area_m2 < 400:
        return (0, 400)
    if plot_area_m2 < 600:
        return (400, 600)
    if plot_area_m2 < 900:
        return (600, 900)
    if plot_area_m2 < 1500:
        return (900, 1500)
    return (1500, 999999)


def compute_land_median(
    moj_rows: List[dict],
    moj_area_names: Set[str],
    date_col: str,
    plot_area_m2: Optional[float] = None,
    window_months: int = DEFAULT_LAND_WINDOW_MONTHS,
) -> Optional[Dict]:
    """Compute land median per m² for the given areas in the time window.

    Per EMPIRICAL_FINDINGS Rule E4: bracket-match the land reference to the
    villa plot size. Smaller plots have higher per-m² land prices, so an
    unbracketed land median would systematically over-classify large-plot
    villas as `luxury_new` and under-classify small-plot villas as
    `land_priced`.

    Strategy:
      1. If plot_area_m2 is given, prefer bracket-matched land sample (24m)
      2. If bracket-matched n<10, widen to area-wide (any bracket, 24m)
      3. If still n<MINIMUM_N_FOR_MEDIAN (=3), fall back to 36m window
      4. Otherwise return None

    Returns:
      {'median_per_m2', 'n', 'window_months', 'bracket_match', 'bracket'} or None
    """
    if not moj_rows or not moj_area_names:
        return None

    # Find latest date (sample first ~5000 rows for speed)
    latest = None
    for r in moj_rows[:5000]:
        d = _parse_date(r.get(date_col, ''))
        if d and (latest is None or d > latest):
            latest = d
    if not latest:
        for r in moj_rows:
            d = _parse_date(r.get(date_col, ''))
            if d and (latest is None or d > latest):
                latest = d
    if not latest:
        return None

    names_normalized = {_norm(n) for n in moj_area_names}
    bracket = _bracket_for_plot(plot_area_m2)

    def _scan(window_m: int, use_bracket: bool) -> List[float]:
        cutoff = latest - timedelta(days=window_m * 30)
        prices = []
        for r in moj_rows:
            area = _norm(r.get('اسم المنطقة', ''))
            if area not in names_normalized:
                continue
            type_ar = r.get('نوع العقار', '')
            if not _is_land(type_ar):
                continue
            d = _parse_date(r.get(date_col, ''))
            if not d or d < cutoff:
                continue
            am = _to_float(r.get('المساحة بالمتر المربع'))
            if not am or am <= 0:
                continue
            if use_bracket and bracket:
                lo, hi = bracket
                if not (lo <= am < hi):
                    continue
            p = _to_float(r.get('سعر المتر المربع'))
            if p and p > 0:
                prices.append(p)
        return prices

    # Try bracket-matched first
    bracket_match = False
    used_window = window_months
    land_prices: List[float] = []
    if bracket:
        land_prices = _scan(window_months, use_bracket=True)
        if len(land_prices) >= RELIABLE_N:
            bracket_match = True
        else:
            # Bracket too thin — widen to area-wide
            land_prices = []

    if not land_prices:
        land_prices = _scan(window_months, use_bracket=False)

    if len(land_prices) < MINIMUM_N_FOR_MEDIAN:
        # Last resort: 36m window, area-wide
        land_prices = _scan(FALLBACK_LAND_WINDOW_MONTHS, use_bracket=False)
        used_window = FALLBACK_LAND_WINDOW_MONTHS

    if len(land_prices) < MINIMUM_N_FOR_MEDIAN:
        return None

    return {
        'median_per_m2':  round(_median(land_prices)),
        'n':              len(land_prices),
        'window_months':  used_window,
        'bracket_match':  bracket_match,
        'bracket':        f'{bracket[0]}-{bracket[1]}' if (bracket and bracket_match) else 'area-wide',
    }


def compute_strata(
    villa_transactions: List[dict],
    land_median_per_m2: float,
    plot_area_m2: Optional[float] = None,
) -> Dict[str, Dict]:
    """Compute per-stratum villa median and estimated total.

    villa_transactions: each must have 'price_m2' (or 'price_per_m2').
    land_median_per_m2: reference land price for ratio computation.
    plot_area_m2: subject plot area (used for 'estimated_total' projection).
    """
    if not villa_transactions or not land_median_per_m2 or land_median_per_m2 <= 0:
        return {}

    buckets = {name: [] for name, _, _ in STRATUM_THRESHOLDS}
    for txn in villa_transactions:
        p = txn.get('price_m2') or txn.get('price_per_m2')
        if not p or p <= 0:
            continue
        ratio = p / land_median_per_m2
        cls = classify_ratio(ratio)
        if cls in buckets:
            buckets[cls].append(p)

    result = {}
    for name, _, _ in STRATUM_THRESHOLDS:
        xs = buckets[name]
        med = _median(xs) if xs else None
        entry = {
            'ratio_band':     _stratum_band_label(name),
            'label_ar':       STRATUM_LABELS_AR[name],
            'description_ar': STRATUM_DESC_AR[name],
            'n':              len(xs),
            'median_per_m2':  round(med) if med else None,
            'reliable':       len(xs) >= RELIABLE_N,
            'reliability_label_ar': (
                'موثوق (n≥10)' if len(xs) >= RELIABLE_N
                else ('إرشادي (n=' + str(len(xs)) + ')' if len(xs) >= MINIMUM_N_FOR_MEDIAN
                      else 'عينة ضعيفة جداً')
            ),
        }
        if plot_area_m2 and med:
            entry['estimated_total'] = round(med * plot_area_m2)
        else:
            entry['estimated_total'] = None
        result[name] = entry
    return result


def classify_subject_property(
    listing_price: Optional[float],
    plot_area_m2: Optional[float],
    land_median_per_m2: Optional[float],
) -> Optional[Dict]:
    """If the user provided a listing_price, place the subject in a stratum.

    Returns None if any input is missing.
    """
    if not listing_price or not plot_area_m2 or not land_median_per_m2:
        return None
    if listing_price <= 0 or plot_area_m2 <= 0 or land_median_per_m2 <= 0:
        return None
    subject_per_m2 = listing_price / plot_area_m2
    ratio = subject_per_m2 / land_median_per_m2
    stratum = classify_ratio(ratio)
    return {
        'listing_price':           round(listing_price),
        'plot_area_m2':            round(plot_area_m2, 1),
        'implied_per_m2':          round(subject_per_m2),
        'land_reference_per_m2':   round(land_median_per_m2),
        'implied_ratio':           round(ratio, 2),
        'classification':          stratum,
        'classification_label_ar': STRATUM_LABELS_AR.get(stratum, stratum),
        'guidance_ar': (
            'سعر العقار الذي أدخلته يضعه في فئة "' + STRATUM_LABELS_AR.get(stratum, stratum) + '". '
            'قارن هذا مع وسيط الفئة في الجدول أدناه: إن كان قريباً منه فالسعر متّسق مع السوق، '
            'وإن كان أعلى بـ 20%+ فالسعر مرتفع لفئته.'
        ),
    }


def build_stock_strata_result(
    moj_rows: Optional[List[dict]],
    moj_area_names: Optional[Set[str]],
    villa_transactions: Optional[List[dict]],
    plot_area_m2: Optional[float],
    listing_price: Optional[float],
    date_col: str,
) -> Optional[Dict]:
    """Main entry point — builds the stock_strata field for API response.

    Returns None if the inputs are insufficient (caller should skip the field).
    """
    if not villa_transactions or len(villa_transactions) < MINIMUM_N_FOR_MEDIAN:
        return None
    if not moj_rows or not moj_area_names:
        return None

    land_ref = compute_land_median(
        moj_rows, moj_area_names, date_col, plot_area_m2=plot_area_m2,
    )
    if not land_ref:
        return None

    land_median = land_ref['median_per_m2']
    strata = compute_strata(villa_transactions, land_median, plot_area_m2)

    # Bail if no stratum got any transactions (would mean every txn fell to 'unknown')
    if not any(s.get('n', 0) > 0 for s in strata.values()):
        return None

    subject = classify_subject_property(listing_price, plot_area_m2, land_median)

    # Identify the dominant stratum (most transactions)
    dominant_name = max(strata.items(), key=lambda kv: kv[1].get('n', 0))[0]
    dominant = strata[dominant_name]

    return {
        'applied':         True,
        'version':         STRATA_VERSION,
        'rule_source':     RULE_SOURCE,
        'methodology_ar': (
            'كل معاملة فيلا تُصنَّف بنسبة سعرها لـ وسيط الأراضي في نفس المنطقة. '
            'هذي النسبة تفصل بين فئات العمر والتشطيب: فيلا قديمة تُباع بسعر الأرض '
            'تقريباً (نسبة ~1.0)، فيلا حديثة جيدة (نسبة ~1.7)، فيلا فاخرة جديدة (نسبة ~2.3+). '
            'القيمة الرئيسية المعروضة في الأعلى تستخدم median المدمج لكل الفئات وهذا محافظ. '
            'الـ stratification في الأسفل شفافية إضافية للمستخدم.'
        ),
        'land_reference': {
            **land_ref,
            'source_ar': 'وسيط معاملات بيع أراضي مسجَّلة في نفس المنطقة (MoJ)',
        },
        'strata':           strata,
        'dominant_stratum': {
            'name':       dominant_name,
            'label_ar':   STRATUM_LABELS_AR.get(dominant_name, dominant_name),
            'n':          dominant.get('n'),
            'share_pct':  round(100 * dominant.get('n', 0) /
                                sum(s.get('n', 0) for s in strata.values()), 1)
                          if sum(s.get('n', 0) for s in strata.values()) else None,
            'note_ar': (
                'الفئة المسيطرة على عينة المنطقة. '
                'median المدمج يميل لتمثيلها أكثر من غيرها — '
                'فإن كانت فيلتك من فئة مختلفة، الرقم الرئيسي قد لا يعكس قيمتها بدقة.'
            ),
        },
        'subject_property': subject,
        # Sprint 2.22.0a.2 C2: removed sprint version self-reference,
        # English/Arabic code-switching (stratification/stratum), and
        # forward-looking-statement promise. Gemini-approved verbatim
        # per docs/MULTI_AI_VALIDATION_BATCH_2p22p0a2.md §2.
        'sprint_scope_caveat_ar': (
            'هذه الطبقات مقدّمة كشفافية إضافية — القيمة الرئيسية أعلاه '
            'لم تتأثّر. اختيار الفئة المناسبة لعقارك حسب العمر والتشطيب '
            'يبقى قرار المستخدم.'
        ),
    }

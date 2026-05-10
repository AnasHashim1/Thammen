#!/usr/bin/env python3
"""
evaluate_property.py — Unified Qatari property evaluation pipeline.

Bridges qatar_gis (what is this property?) with moj_reference (what is it worth?)
and investment_model (does the deal make sense?). Produces one verdict from one
address.

Strategy by asset type:
    STANDALONE_VILLA → MoJ "villa" lookup, size-bracket match
    RAW_LAND         → MoJ "land" lookup, size-bracket match
    PALACE           → MoJ "palace" if present, else "villa" 1500+ bracket
    COMPOUND_SMALL   → MoJ "مجمع فلل" if n≥10, else DCF template
    COMPOUND_LARGE   → DCF template (no MoJ comparable)
    APARTMENT_BUILD  → DCF template
    TOWER            → DCF template
    COMMERCIAL       → DCF template + commercial caveat
    INDUSTRIAL       → DCF template + industrial caveat
    AGRICULTURAL     → Out of scope warning
    UNKNOWN          → Manual review required

Usage:
    python3 evaluate_property.py <zone> <street> <building> \\
        --moj-csv <path> \\
        [--listing-price <price>] [--listing-area <m2>] \\
        [--listing-description <text>] \\
        [--output-dir ./eval_output]

Produces in --output-dir:
    <addr>_evaluation.json     Full structured result (always)
    <addr>_report.docx         Human-readable report (if python-docx available)
    <addr>_deal_template.json  Pre-filled DCF input (only for income-producing types)
"""

import argparse
import json
import re
import sys
from dataclasses import dataclass, asdict, field
from datetime import datetime
from pathlib import Path
from typing import Optional

# Soft imports — fail at runtime, not at import, so the module is testable
# even when the project's qatar_gis isn't on PYTHONPATH.
try:
    from qatar_gis import QatarGIS, AssetType, PropertyReport
    _GIS_AVAILABLE = True
except ImportError:
    _GIS_AVAILABLE = False

# moj_reference is a sibling script. We need its build_reference function.
try:
    from moj_reference import build_reference, parse_date, MIN_N, compute_trend
    _MOJ_AVAILABLE = True
except ImportError:
    _MOJ_AVAILABLE = False

# property_factors is an optional, GIS-driven adjustment layer. If available,
# we apply ±10% adjustments per the expert rule based on objective GIS factors
# (Zoning, sewage proximity, plot shape, optionally building age).
try:
    from property_factors import analyze_property as analyze_factors
    _FACTORS_AVAILABLE = True
except ImportError:
    _FACTORS_AVAILABLE = False

# ── Thammen v2 modules ──
# Three new modules that move the system from "valuation engine" to
# "market intelligence platform with full transparency":
#   1. service_charge_db: verified per-precinct service charges (FGRealty data)
#   2. market_position:   descriptive position (no buy/sell verdicts)
#   3. reasoning_trace:   full chain of facts + sources + disclaimer
try:
    import service_charge_db
    import market_position
    from reasoning_trace import (
        ReasoningTrace,
        build_from_moj_valuation,
        build_from_replacement_cost,
        build_from_listing_comparison,
        build_from_listing_flags,
        add_standard_unknowns,
    )
    _V2_MODULES_AVAILABLE = True
except ImportError:
    _V2_MODULES_AVAILABLE = False


# Hardcoded GIS→MoJ name overrides for areas where the canonical MoJ name
# differs from GIS in a way that's not just "drop the ال".
# Per system prompt §3.
GIS_TO_MOJ_NAME_OVERRIDES = {
    # GIS name → MoJ name
    'أبو هامور': 'بو هامور',
    'ابو هامور': 'بو هامور',
    'أم قرن': 'ام قرن',
    'ام قرن': 'ام قرن',
}


def _candidate_moj_names(gis_name: str) -> list:
    """
    Generate candidate MoJ area-name strings for a single GIS name.

    Returns variants in priority order:
      1. exact match
      2. without leading 'ال'
      3. hardcoded override from GIS_TO_MOJ_NAME_OVERRIDES
    """
    candidates = []
    if not gis_name:
        return candidates
    name = gis_name.strip()
    candidates.append(name)
    # Leading 'ال' variant
    if name.startswith('ال'):
        candidates.append(name[2:])
    else:
        # If it doesn't start with ال, also try with it (in case GIS dropped it)
        candidates.append('ال' + name)
    # Hardcoded override
    override = GIS_TO_MOJ_NAME_OVERRIDES.get(name)
    if override:
        candidates.append(override)
    # Dedupe preserving order
    seen = []
    for c in candidates:
        if c not in seen:
            seen.append(c)
    return seen


def resolve_moj_area_name(rows: list, gis_name: str) -> Optional[tuple]:
    """
    Find the matching MoJ area name for a single GIS district name.

    GIS is the sole authority. We do NOT substitute aliases or popular
    market names. We only normalize trivial variations:
      - exact match
      - drop leading 'ال'
      - hardcoded overrides for areas where MoJ uses a known different
        spelling (e.g. أبو هامور → بو هامور)

    Returns (best_name, transaction_count) or None.
    """
    import re
    def normalize(s):
        return re.sub(r'\s+', ' ', s or '').strip()

    # Build tally of area-names actually present in MoJ
    moj_areas = {}
    for r in rows:
        a = normalize(r.get('اسم المنطقة', ''))
        if a:
            moj_areas[a] = moj_areas.get(a, 0) + 1

    # Try variants of the single GIS name
    best = None
    for variant in _candidate_moj_names(gis_name):
        n_variant = normalize(variant)
        # Exact match
        if n_variant in moj_areas:
            count = moj_areas[n_variant]
            if best is None or count > best[1]:
                best = (n_variant, count)
        # Sub-zone matches (e.g. 'الثمامة 46', 'ازغوى 51')
        # NOTE: We only match these if the user explicitly asks.
        # Auto-resolution sticks to the parent name for stability.
    return best


# ============================================================
# 1. CONFIGURATION
# ============================================================

# Map AssetType → MoJ category and lookup hint.
# The hint is what build_reference returns under categories[X].
ASSET_TYPE_TO_MOJ_CATEGORY = {
    'standalone_villa': 'villa',
    'palace':           'villa',   # fallback; real MoJ has no 'palace' category
    'compound_small':   'villa',   # we'll filter to 'مجمع فلل' separately if available
    'raw_land':         'land',
    # These have no direct MoJ comparable — DCF only:
    'compound_large':   None,
    'apartment_building': None,
    'tower':            None,
    'commercial':       None,
    'industrial':       None,
    'agricultural':     None,
    'unknown':          None,
}

# Asset types for which a DCF deal_template is the right tool
DCF_REQUIRED_TYPES = {
    'compound_large', 'compound_small', 'apartment_building',
    'tower', 'commercial', 'industrial',
}

# Size brackets must match moj_reference.py exactly
SIZE_BRACKETS = [(0,400),(400,600),(600,900),(900,1500),(1500,99999)]

# ---- Replacement Cost defaults (Qatar 2024-2026) ----
# Source: local contractor estimates + user-validated cases.
CONSTRUCTION_COST_PER_M2 = {
    'low':    2500,   # basic finishing
    'mid':    3000,   # standard finishing
    'high':   3800,   # luxury finishing
}

# Calibrated costs file (generated by calibrate_construction_cost.py)
_CALIBRATED_COSTS = None

def _load_calibrated_costs(search_paths=None) -> dict:
    """Load calibrated construction costs from JSON if available."""
    global _CALIBRATED_COSTS
    if _CALIBRATED_COSTS is not None:
        return _CALIBRATED_COSTS

    paths = search_paths or [
        Path(__file__).parent / 'construction_costs.json',
        Path.cwd() / 'construction_costs.json',
    ]
    for p in paths:
        if p.exists():
            try:
                data = json.loads(p.read_text(encoding='utf-8'))
                _CALIBRATED_COSTS = data.get('municipalities', {})
                return _CALIBRATED_COSTS
            except Exception:
                pass
    _CALIBRATED_COSTS = {}
    return _CALIBRATED_COSTS


def get_construction_cost(tier: str = 'mid', municipality: str = None) -> float:
    """
    Get construction cost per BUA m².

    If calibrated data exists for the municipality, use it.
    Otherwise fall back to the static constant.
    """
    calibrated = _load_calibrated_costs()
    if municipality and municipality in calibrated:
        muni_data = calibrated[municipality]
        bua_stats = muni_data.get('cost_per_bua_m2_estimated', {})
        if tier == 'low':
            return bua_stats.get('p25', CONSTRUCTION_COST_PER_M2['low'])
        elif tier == 'high':
            return bua_stats.get('p75', CONSTRUCTION_COST_PER_M2['high'])
        else:
            return bua_stats.get('median', CONSTRUCTION_COST_PER_M2['mid'])

    return CONSTRUCTION_COST_PER_M2.get(tier, CONSTRUCTION_COST_PER_M2['mid'])
# Per-component cost multipliers (applied ON TOP of the tier base).
# Validated against: standard contractor (2,500/m²) and J Seven (3,500/m²).
COMPONENT_COST_MULTIPLIERS = {
    'basement':   1.17,   # ~3,500/m² at mid — excavation + waterproofing
    'upper':      0.93,   # ~2,790/m² — no foundation
    'ground':     1.00,   # baseline
    'annex':      0.73,   # ~2,190/m² — simple single-story
    'external':   0.60,   # ~1,800/m² — مجلس/مطبخ خارجي (was 0.67, adjusted)
}
DEPRECIATION_RATE_PER_YEAR = 0.02          # legacy flat rate (replaced by curve below)
RENOVATION_RECOVERY_PCT = 0.15             # partial renovation recovers ~15% (was 12%)
FULL_RENOVATION_RECOVERY_PCT = 0.40        # full interior+exterior reno recovers ~40% (was 30%)
EXTERNAL_WORKS_COST = 250000               # سور + بوابة + بلاط خارجي + تنسيق (QAR)
POOL_VALUE = 80000                         # مسبح عادي (QAR)
COMPOUND_DISCOUNT = 0.17                   # كومباوند أرخص 17% من فيلا مستقلة
# BUA/plot ratio thresholds for blending weight
TYPICAL_BUA_RATIO = (0.45, 0.80)           # typical single-floor or 1.5-floor villa
HIGH_BUA_RATIO_THRESHOLD = 1.0             # above this → replacement cost gets majority weight

# Setback rules (Qatar Municipality — residential)
SETBACK_FRONT = 5    # meters
SETBACK_SIDE = 3     # meters (each side)
SETBACK_BACK = 3     # meters


# Red flag keywords (Arabic). Each is a tuple of (pattern, severity, label).
# severity: 'exclude' triggers immediate disqualification; 'warn' is for inspection
RED_FLAGS = [
    (r'بسعر\s*الأرض|سعر\s*الأرض', 'exclude', 'البناء بقيمة صفر — قيد للهدم'),
    (r'بيت\s*شعبي', 'exclude', 'بيت شعبي قديم'),
    (r'(?:ل?ل?هدم|هدمه)', 'exclude', 'مرشح للهدم'),
    (r'تنازل', 'exclude', 'تنازل — السعر المُعلَن لا يساوي السعر الفعلي'),
    (r'أقساط\s*متبقية|اقساط\s*متبقيه', 'exclude', 'أقساط متبقية على البائع'),
    (r'بدون\s*فرز|خلاف', 'exclude', 'تعقيدات قانونية'),
    (r'قديم[ةه]?', 'warn', 'البائع يصرّح بأن العقار قديم'),
    (r'فيلتين\s*متلاصقات?', 'warn', 'مبنى استثماري لا فيلا عائلية'),
    (r'يحتاج\s*(?:ترميم|صيانة)', 'warn', 'يحتاج صيانة — أضف تكلفة الترميم'),
]

# Green flag keywords
GREEN_FLAGS = [
    (r'حديث\s*البناء|بناء\s*حديث', 'بناء حديث — حالة أفضل'),
    (r'لم\s*[تي]ُ?سكن', 'لم تُسكن — حالة جديدة'),
    (r'تشطيب\s*جديد|مرمم[ةه]?', 'مُرمَّم قبل البيع'),
    (r'فاخر[ةه]?|ديلوكس', 'تشطيب فاخر'),
    (r'مسبح', 'يحتوي على مسبح'),
    (r'مباشر\s*من\s*المالك', 'بيع مباشر — توفير عمولة الوسيط ٢.٥٪'),
    (r'على\s*شارعين|زاوي[ةه]', 'قطعة زاوية / على شارعين — علاوة ١٠-١٥٪'),
    (r'رخصة\s*بناء\s*حديث[ةه]?', 'رخصة بناء حديثة — جاهز للبناء'),
]


# ============================================================
# 2. DATA CLASSES
# ============================================================

@dataclass
class ListingFlags:
    """Flags extracted from a free-text listing description."""
    red_flags: list                # list of (pattern, severity, label)
    green_flags: list              # list of (pattern, label)
    has_excluding_red_flag: bool   # any severity == 'exclude'


@dataclass
class MoJValuation:
    """MoJ-based valuation for an asset."""
    strategy: str                          # human label of which strategy was used
    moj_category: Optional[str]            # 'villa' | 'land' | None
    size_bracket: Optional[str]            # e.g. '400-600'
    bracket_n: Optional[int]               # sample size in bracket
    bracket_reliable: Optional[bool]       # n >= 10
    moj_median_per_m2: Optional[float]
    moj_median_total: Optional[float]
    estimated_value_low: Optional[float]   # plot_area × p25
    estimated_value_median: Optional[float]
    estimated_value_high: Optional[float]  # plot_area × p75
    # Fair-price layer (added when property_factors is available)
    factors_adjustment: Optional[float] = None      # e.g. +0.05 or -0.02
    fair_price_total: Optional[float] = None        # MoJ median × (1 + adjustment)
    fair_price_per_m2: Optional[float] = None       # for per-m² view
    factors_detail: Optional[list] = None           # list of factor dicts
    notes: list = field(default_factory=list)


@dataclass
class BuaBreakdown:
    """Built-up area broken down by construction component.

    Main building: footprint × floors (basement, ground, upper floors).
    Annexes: separate single-story structures (ملاحق).
    External: مجلس خارجي، مطبخ خارجي، etc.
    """
    main_footprint_m2: float = 0         # ground-floor footprint of main building
    basement_m2: float = 0               # basement area (usually ≈ main footprint)
    upper_floors_m2: float = 0           # total area of floors above ground
    upper_floor_count: int = 0           # how many upper floors
    annexes_m2: float = 0                # total built-up of all annexes (single-story)
    annex_count: int = 0                 # number of annexes
    external_m2: float = 0              # مجلس خارجي + مطبخ خارجي etc.

    @property
    def total_bua(self) -> float:
        return (self.main_footprint_m2 + self.basement_m2 +
                self.upper_floors_m2 + self.annexes_m2 + self.external_m2)

    @property
    def main_bua(self) -> float:
        """Total BUA of the main building only (all floors)."""
        return self.main_footprint_m2 + self.basement_m2 + self.upper_floors_m2


@dataclass
class ReplacementCostValuation:
    """Replacement-cost approach: land value + depreciated building value.

    When BUA breakdown is available, each component uses its own cost/m².
    This matters because a basement costs ~17% more than ground floor,
    while annexes cost ~27% less (simple single-story construction).
    """
    land_value: float
    land_price_per_m2: float
    bua_m2: float                              # total BUA
    bua_breakdown: Optional[BuaBreakdown]      # component-level detail
    bua_plot_ratio: float
    # Per-component cost detail (when breakdown available)
    component_costs: Optional[list]            # list of {component, area, cost_per_m2, subtotal}
    construction_cost_new: float               # total new-build cost
    building_age_years: Optional[int]
    depreciation_pct: float
    renovation_recovery_pct: float
    depreciated_building_value: float
    total_replacement_value: float
    notes: list = field(default_factory=list)


@dataclass
class BlendedValuation:
    """Final blended valuation when both MoJ and replacement cost are available."""
    moj_value: Optional[float]
    replacement_value: Optional[float]
    moj_weight: float                          # 0.0 to 1.0
    replacement_weight: float                  # 1.0 - moj_weight
    blended_value: float                       # weighted average
    blended_low: Optional[float]               # range low
    blended_high: Optional[float]              # range high
    blend_reason: str                          # why this weighting was chosen
    notes: list = field(default_factory=list)


@dataclass
class ListingComparison:
    """Compare a listing's price against MoJ reference (or fair_price if factors available)."""
    listing_price: float
    listing_area_m2: Optional[float]
    moj_median_total: float
    # If factors-based fair price is available, we compare against that;
    # otherwise we fall back to MoJ median.
    benchmark_total: float                 # the actual number compared against
    benchmark_label: str                   # 'MoJ median' or 'fair price (MoJ + factors)'
    gap_qar: float                         # listing - benchmark
    gap_pct: float                         # gap / benchmark
    above_buyer_ceiling: bool              # listing > benchmark × 1.10
    above_market_ceiling: bool             # listing > benchmark × 1.30
    verdict_label: str                     # 'BARGAIN' | 'AT_MARKET' | 'OVERPRICED' | 'REJECT'


@dataclass
class PropertyEvaluation:
    """The unified output of evaluate_property() — Thammen v2.

    v2 changes vs v1:
      - `verdict` field DEPRECATED (kept for backward compat, will be empty)
      - new `market_position` field: descriptive position only
      - new `reasoning_trace` field: full chain of facts + sources
      - new `disclaimer` field: legal protection text
    """
    address: str
    asset_type: str
    classification_confidence: str
    plot_area_m2: Optional[float]
    extent_total_m2: Optional[float]

    # GIS district — sole authority for area name
    gis_district_aname: Optional[str] = None
    gis_district_ename: Optional[str] = None
    gis_district_no: Optional[int] = None
    moj_area_name: Optional[str] = None     # what we actually queried in MoJ

    valuation: Optional[MoJValuation] = None
    replacement_cost: Optional[ReplacementCostValuation] = None
    blended: Optional[BlendedValuation] = None
    listing_comparison: Optional[ListingComparison] = None
    listing_flags: Optional[ListingFlags] = None

    requires_dcf: bool = False
    dcf_template_path: Optional[str] = None
    trend: Optional[dict] = None          # annual price-per-foot trend

    # Confidence score (0-100) — kept but reframed as data quality, not value confidence
    confidence_score: Optional[int] = None
    confidence_label: Optional[str] = None
    confidence_breakdown: Optional[dict] = None

    # Rental analysis
    rental_analysis: Optional[dict] = None
    valuation_date: Optional[str] = None     # ISO date of valuation

    # ── v2 new fields ──
    market_position: Optional[dict] = None   # MarketPosition.to_dict() — descriptive
    reasoning_trace: Optional[dict] = None   # ReasoningTrace.to_dict() — full transparency
    disclaimer: str = (
        "ثمّن يجمع البيانات السوقية من المصادر الحكومية والإعلانات النشطة. "
        "هذا تحليل معلوماتي للقرار، وليس تقييماً عقارياً معتمداً وفق RICS/IVS. "
        "للأغراض الرسمية (قروض، محاكم، تقارير محاسبية) يلزم مُقيِّم معتمد."
    )
    valuation_id: str = ''                   # unique ID for audit trail

    # ── v1 backward-compat fields (will be empty in v2 but kept to not break consumers) ──
    verdict: str = ''                          # DEPRECATED — use market_position instead
    reasons: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    raw_property_report: Optional[dict] = None


# ============================================================
# 3. LISTING DESCRIPTION ANALYSIS
# ============================================================

def analyze_listing_description(description: str) -> ListingFlags:
    """Run regex flag detection on a listing description (Arabic)."""
    if not description:
        return ListingFlags(red_flags=[], green_flags=[], has_excluding_red_flag=False)

    desc = description.strip()
    found_red = []
    for pattern, severity, label in RED_FLAGS:
        if re.search(pattern, desc):
            found_red.append({'pattern': pattern, 'severity': severity, 'label': label})

    found_green = []
    for pattern, label in GREEN_FLAGS:
        if re.search(pattern, desc):
            found_green.append({'pattern': pattern, 'label': label})

    has_excluding = any(f['severity'] == 'exclude' for f in found_red)

    return ListingFlags(
        red_flags=found_red,
        green_flags=found_green,
        has_excluding_red_flag=has_excluding,
    )


# ============================================================
# 4. MoJ STRATEGY RESOLUTION
# ============================================================

def _bracket_for_area(area_m2: float) -> str:
    for lo, hi in SIZE_BRACKETS:
        if lo <= area_m2 < hi:
            return f'{lo}-{hi}'
    return f'{SIZE_BRACKETS[-1][0]}-{SIZE_BRACKETS[-1][1]}'


def _safe_get(d, *keys, default=None):
    """Walk a nested dict safely."""
    for k in keys:
        if not isinstance(d, dict) or k not in d:
            return default
        d = d[k]
    return d if d is not None else default


def apply_moj_strategy(asset_type: str, plot_area_m2: float,
                        moj_reference: dict) -> MoJValuation:
    """
    Look up MoJ valuation for a given asset_type + plot area.

    moj_reference is the JSON output of moj_reference.py (the per-area dict).
    """
    moj_cat = ASSET_TYPE_TO_MOJ_CATEGORY.get(asset_type)
    if moj_cat is None:
        return MoJValuation(
            strategy=f'No MoJ comparable for {asset_type} — DCF required',
            moj_category=None, size_bracket=None,
            bracket_n=None, bracket_reliable=None,
            moj_median_per_m2=None, moj_median_total=None,
            estimated_value_low=None, estimated_value_median=None,
            estimated_value_high=None,
            notes=[f'Asset type {asset_type} has no direct MoJ benchmark'],
        )

    cat_data = _safe_get(moj_reference, 'categories', moj_cat, default={})
    if not cat_data or cat_data.get('n', 0) == 0:
        return MoJValuation(
            strategy=f'MoJ {moj_cat} lookup',
            moj_category=moj_cat, size_bracket=None,
            bracket_n=0, bracket_reliable=False,
            moj_median_per_m2=None, moj_median_total=None,
            estimated_value_low=None, estimated_value_median=None,
            estimated_value_high=None,
            notes=[f'No MoJ {moj_cat} transactions available for this area'],
        )

    bracket_key = _bracket_for_area(plot_area_m2)
    bracket = _safe_get(cat_data, 'size_brackets', bracket_key, default={})

    # Use bracket if reliable, otherwise fall back to overall category stats
    notes = []
    if bracket and bracket.get('n', 0) >= 10:
        n = bracket['n']
        per_m2 = bracket.get('price_per_m2_median')
        total_median = bracket.get('total_price_median')
        reliable = True
        strategy_label = f'MoJ {moj_cat} ({bracket_key} m², n={n})'
    elif bracket and bracket.get('n', 0) > 0:
        n = bracket['n']
        per_m2 = bracket.get('price_per_m2_median')
        total_median = bracket.get('total_price_median')
        reliable = False
        notes.append(f'Bracket sample n={n} < 10 — indicative only')
        strategy_label = f'MoJ {moj_cat} ({bracket_key} m², n={n}, indicative)'
    else:
        # Fall back to overall category
        n = cat_data.get('n', 0)
        per_m2 = _safe_get(cat_data, 'price_per_m2', 'median')
        total_median = _safe_get(cat_data, 'total_price', 'median')
        reliable = n >= 20
        notes.append(f'No transactions in bracket {bracket_key}; using overall {moj_cat} median')
        strategy_label = f'MoJ {moj_cat} (overall, n={n})'

    # Build estimated value range — keep all three numbers from the SAME level
    # to avoid the inversion bug where bracket-median > category-p75.
    bracket_p25 = _safe_get(bracket, 'price_per_m2_p25')
    bracket_p75 = _safe_get(bracket, 'price_per_m2_p75')
    bracket_total_p25 = _safe_get(bracket, 'total_price_p25')
    bracket_total_p75 = _safe_get(bracket, 'total_price_p75')

    if bracket_total_p25 is not None and bracket_total_p75 is not None:
        # Best: use total_price quartiles directly from the bracket
        est_low = bracket_total_p25
        est_median = total_median
        est_high = bracket_total_p75
        range_source = 'bracket total_price quartiles'
    elif bracket_p25 is not None and bracket_p75 is not None:
        # Next-best: bracket per-m² quartiles × plot area
        est_low = plot_area_m2 * bracket_p25
        est_median = plot_area_m2 * per_m2 if per_m2 else None
        est_high = plot_area_m2 * bracket_p75
        range_source = 'bracket price_per_m2 quartiles'
    else:
        # Fallback: category-level quartiles. NOT mixed with bracket median —
        # if we use category quartiles, we use the category median too.
        cat_p25 = _safe_get(cat_data, 'price_per_m2', 'p25')
        cat_med = _safe_get(cat_data, 'price_per_m2', 'median')
        cat_p75 = _safe_get(cat_data, 'price_per_m2', 'p75')
        if cat_p25 and cat_p75:
            est_low = plot_area_m2 * cat_p25
            est_median = plot_area_m2 * cat_med if cat_med else None
            est_high = plot_area_m2 * cat_p75
            range_source = f'category-level quartiles (no bracket data)'
            notes.append(
                'Value range uses category-level quartiles (mixes other size brackets). '
                'Use median, not range, for negotiation reference.'
            )
        else:
            est_low = est_median = est_high = None
            range_source = 'unavailable'

    # Sanity: ensure low ≤ median ≤ high. If reordering needed, surface it.
    vals = [v for v in (est_low, est_median, est_high) if v is not None]
    if len(vals) == 3 and not (est_low <= est_median <= est_high):
        notes.append(
            f'Range inversion detected (low={est_low:,.0f}, median={est_median:,.0f}, '
            f'high={est_high:,.0f}). Source: {range_source}.'
        )

    return MoJValuation(
        strategy=strategy_label,
        moj_category=moj_cat,
        size_bracket=bracket_key,
        bracket_n=n,
        bracket_reliable=reliable,
        moj_median_per_m2=per_m2,
        moj_median_total=total_median,
        estimated_value_low=est_low,
        estimated_value_median=est_median,
        estimated_value_high=est_high,
        notes=notes,
    )


# ============================================================
# 4b. REPLACEMENT COST VALUATION (requires BUA)
# ============================================================

def compute_replacement_cost(
    plot_area_m2: float,
    moj_land_median_per_m2: Optional[float],
    building_age_years: Optional[int] = None,
    construction_tier: str = 'mid',
    has_renovation: bool = False,
    full_renovation: bool = False,
    municipality: Optional[str] = None,
    # Accept EITHER flat BUA or breakdown (breakdown takes precedence)
    bua_m2: Optional[float] = None,
    bua_breakdown: Optional[BuaBreakdown] = None,
) -> ReplacementCostValuation:
    """
    Compute property value using the replacement cost approach:
        Value = Land value + Depreciated building value

    When bua_breakdown is provided, each component (basement, ground,
    upper, annex, external) is costed at its own rate. This is critical
    because annexes (single-story, simple construction) cost ~27% less
    per m² than the main building, while basements cost ~17% more.

    When only flat bua_m2 is provided, the tier rate is applied uniformly
    (backward compatible).
    """
    notes = []

    # Land value
    if moj_land_median_per_m2 is None or moj_land_median_per_m2 <= 0:
        notes.append('No MoJ land reference available — land value set to 0')
        land_per_m2 = 0
        land_value = 0
    else:
        land_per_m2 = moj_land_median_per_m2
        land_value = plot_area_m2 * land_per_m2

    # Resolve total BUA
    if bua_breakdown:
        total_bua = bua_breakdown.total_bua
    elif bua_m2:
        total_bua = bua_m2
    else:
        total_bua = 0

    bua_ratio = total_bua / plot_area_m2 if plot_area_m2 > 0 else 0
    if bua_ratio > 1.5:
        notes.append(
            f'BUA/plot ratio = {bua_ratio:.2f} — multi-story with basement. '
            f'MoJ per-plot comparisons will undervalue this property.'
        )
    elif bua_ratio > 1.0:
        notes.append(f'BUA/plot ratio = {bua_ratio:.2f} — multi-story building.')

    # Construction cost — per-component or flat
    base_cost = get_construction_cost(construction_tier, municipality)
    if municipality and municipality in _load_calibrated_costs():
        notes.append(f'تكلفة بناء مُعايَرة لبلدية {municipality}: {base_cost:,.0f}/م²')
    component_costs = None

    if bua_breakdown:
        # Per-component costing
        components = []
        if bua_breakdown.basement_m2 > 0:
            c = base_cost * COMPONENT_COST_MULTIPLIERS['basement']
            components.append({
                'component': 'سرداب (basement)',
                'area_m2': bua_breakdown.basement_m2,
                'cost_per_m2': round(c),
                'subtotal': round(bua_breakdown.basement_m2 * c),
            })
        if bua_breakdown.main_footprint_m2 > 0:
            c = base_cost * COMPONENT_COST_MULTIPLIERS['ground']
            components.append({
                'component': 'أرضي (ground)',
                'area_m2': bua_breakdown.main_footprint_m2,
                'cost_per_m2': round(c),
                'subtotal': round(bua_breakdown.main_footprint_m2 * c),
            })
        if bua_breakdown.upper_floors_m2 > 0:
            label = f'طوابق علوية ×{bua_breakdown.upper_floor_count}' if bua_breakdown.upper_floor_count else 'طوابق علوية'
            c = base_cost * COMPONENT_COST_MULTIPLIERS['upper']
            components.append({
                'component': label,
                'area_m2': bua_breakdown.upper_floors_m2,
                'cost_per_m2': round(c),
                'subtotal': round(bua_breakdown.upper_floors_m2 * c),
            })
        if bua_breakdown.annexes_m2 > 0:
            label = f'ملاحق ×{bua_breakdown.annex_count}' if bua_breakdown.annex_count else 'ملاحق'
            c = base_cost * COMPONENT_COST_MULTIPLIERS['annex']
            components.append({
                'component': label,
                'area_m2': bua_breakdown.annexes_m2,
                'cost_per_m2': round(c),
                'subtotal': round(bua_breakdown.annexes_m2 * c),
            })
        if bua_breakdown.external_m2 > 0:
            c = base_cost * COMPONENT_COST_MULTIPLIERS['external']
            components.append({
                'component': 'مجلس/مطبخ خارجي',
                'area_m2': bua_breakdown.external_m2,
                'cost_per_m2': round(c),
                'subtotal': round(bua_breakdown.external_m2 * c),
            })

        cost_new = sum(c['subtotal'] for c in components)
        component_costs = components
        weighted_avg = cost_new / total_bua if total_bua > 0 else base_cost
        notes.append(
            f'Component costing: weighted avg {weighted_avg:,.0f}/m² '
            f'(vs flat {base_cost:,.0f}/m²)'
        )
    else:
        # Flat costing (backward compatible)
        cost_new = total_bua * base_cost

    # Depreciation — accelerating curve (validated against MEP system lifecycles)
    age = building_age_years or 0
    if age <= 10:
        depreciation = age * 0.015          # 1.5%/yr — building young
    elif age <= 20:
        depreciation = 0.15 + (age - 10) * 0.020  # 2%/yr — first MEP replacements
    elif age <= 30:
        depreciation = 0.35 + (age - 20) * 0.030  # 3%/yr — major overhaul needed
    else:
        depreciation = min(0.65 + (age - 30) * 0.020, 0.80)  # cap at 80%

    # Renovation recovery
    if full_renovation:
        recovery = FULL_RENOVATION_RECOVERY_PCT
        notes.append(f'ترميم شامل → استرداد {FULL_RENOVATION_RECOVERY_PCT*100:.0f}% من الإهلاك')
    elif has_renovation:
        recovery = RENOVATION_RECOVERY_PCT
        notes.append(f'ترميم جزئي → استرداد {RENOVATION_RECOVERY_PCT*100:.0f}% من الإهلاك')
    else:
        recovery = 0.0

    net_depreciation = max(0, depreciation - recovery)
    depreciated_value = cost_new * (1 - net_depreciation)

    # External works (wall, gate, landscaping) — always present in Qatar villas
    external_works = EXTERNAL_WORKS_COST if total_bua > 0 else 0
    total = land_value + depreciated_value + external_works

    if external_works > 0:
        notes.append(f'أعمال خارجية (سور + بوابة + تنسيق): {external_works:,.0f} ر.ق')

    if age > 0:
        notes.append(
            f'عمر البناء ~{age} سنة → إهلاك {depreciation*100:.0f}% '
            f'- استرداد {recovery*100:.0f}% = صافي {net_depreciation*100:.0f}%'
        )

    return ReplacementCostValuation(
        land_value=round(land_value),
        land_price_per_m2=round(land_per_m2),
        bua_m2=total_bua,
        bua_breakdown=bua_breakdown,
        bua_plot_ratio=round(bua_ratio, 2),
        component_costs=component_costs,
        construction_cost_new=round(cost_new),
        building_age_years=age if age > 0 else None,
        depreciation_pct=round(depreciation, 3),
        renovation_recovery_pct=round(recovery, 3),
        depreciated_building_value=round(depreciated_value),
        total_replacement_value=round(total),
        notes=notes,
    )


def blend_valuations(
    moj_val: Optional[MoJValuation],
    repl_val: Optional[ReplacementCostValuation],
    bua_plot_ratio: float,
    bracket_n: Optional[int],
) -> Optional[BlendedValuation]:
    """
    Blend MoJ comparable and replacement cost approaches.

    Weighting logic:
      - Normal BUA ratio (0.4-0.8) + reliable MoJ (n≥10): MoJ 80%, Repl 20%
      - Normal BUA ratio + weak MoJ (n<10): MoJ 60%, Repl 40%
      - High BUA ratio (>1.0) + any MoJ: MoJ 30%, Repl 70%
      - High BUA ratio + weak MoJ: MoJ 20%, Repl 80%
      - No MoJ available: Repl 100%
      - No Repl available: MoJ 100%
    """
    moj_total = None
    if moj_val and moj_val.moj_median_total:
        moj_total = moj_val.moj_median_total
        # Use fair_price if factors adjustment is available
        if moj_val.fair_price_total:
            moj_total = moj_val.fair_price_total

    repl_total = repl_val.total_replacement_value if repl_val else None

    if moj_total is None and repl_total is None:
        return None

    if moj_total is None:
        return BlendedValuation(
            moj_value=None, replacement_value=repl_total,
            moj_weight=0.0, replacement_weight=1.0,
            blended_value=repl_total,
            blended_low=round(repl_total * 0.90),
            blended_high=round(repl_total * 1.10),
            blend_reason='No MoJ comparable — using replacement cost only',
            notes=[],
        )

    if repl_total is None:
        return BlendedValuation(
            moj_value=moj_total, replacement_value=None,
            moj_weight=1.0, replacement_weight=0.0,
            blended_value=moj_total,
            blended_low=round(moj_total * 0.90),
            blended_high=round(moj_total * 1.10),
            blend_reason='No BUA provided — using MoJ comparable only',
            notes=[],
        )

    # Both available — compute weights
    n = bracket_n or 0
    reliable_moj = n >= 10
    high_bua = bua_plot_ratio > HIGH_BUA_RATIO_THRESHOLD

    if high_bua and not reliable_moj:
        moj_w, repl_w = 0.20, 0.80
        reason = (
            f'High BUA/plot ratio ({bua_plot_ratio:.2f}) + weak MoJ sample (n={n}) '
            f'→ replacement cost dominant'
        )
    elif high_bua:
        moj_w, repl_w = 0.30, 0.70
        reason = (
            f'High BUA/plot ratio ({bua_plot_ratio:.2f}) '
            f'→ MoJ per-plot comparison undervalues building mass'
        )
    elif not reliable_moj:
        moj_w, repl_w = 0.60, 0.40
        reason = f'Weak MoJ sample (n={n}) → replacement cost as secondary anchor'
    else:
        moj_w, repl_w = 0.80, 0.20
        reason = 'Normal BUA ratio + reliable MoJ → MoJ dominant with replacement sanity check'

    blended = moj_w * moj_total + repl_w * repl_total
    # Range: min/max of the two approaches, with 5% buffer
    low = round(min(moj_total, repl_total) * 0.95)
    high = round(max(moj_total, repl_total) * 1.05)

    notes = []
    gap_pct = abs(moj_total - repl_total) / min(moj_total, repl_total)
    if gap_pct > 0.25:
        notes.append(
            f'MoJ and replacement cost diverge by {gap_pct*100:.0f}%. '
            f'This usually means the building is unusually large or small for its plot. '
            f'Physical inspection strongly recommended.'
        )

    return BlendedValuation(
        moj_value=round(moj_total),
        replacement_value=round(repl_total),
        moj_weight=moj_w, replacement_weight=repl_w,
        blended_value=round(blended),
        blended_low=low, blended_high=high,
        blend_reason=reason, notes=notes,
    )


# ============================================================
# 5. LISTING ↔ MoJ COMPARISON
# ============================================================

def compare_listing_to_moj(listing_price: float,
                            listing_area_m2: Optional[float],
                            valuation: MoJValuation,
                            plot_area_m2: float) -> Optional[ListingComparison]:
    """Compare a listing price to MoJ reference (or fair_price if available)."""
    if valuation.moj_median_total is None and valuation.moj_median_per_m2 is None:
        return None

    # MoJ baseline
    if valuation.moj_median_total is not None:
        moj_total = valuation.moj_median_total
    else:
        moj_total = valuation.moj_median_per_m2 * plot_area_m2

    # If property_factors gave us a fair_price, use it as the benchmark.
    # Otherwise use MoJ median directly (legacy behavior).
    if valuation.fair_price_total is not None:
        benchmark = valuation.fair_price_total
        benchmark_label = (
            f'fair price (MoJ × {1 + valuation.factors_adjustment:.3f})'
        )
    else:
        benchmark = moj_total
        benchmark_label = 'MoJ median'

    gap = listing_price - benchmark
    gap_pct = gap / benchmark if benchmark else 0

    # Verdict thresholds (per system prompt §12 + expert rule):
    # - Buyer ceiling: benchmark + 10%  → above this requires strong justification
    # - Market ceiling: benchmark + 30% → above this is unsellable
    above_buyer = listing_price > benchmark * 1.10
    above_market = listing_price > benchmark * 1.30

    # Tighter bands when we use fair_price (factors already absorbed property's
    # objective premium, so deviation should be smaller).
    if valuation.fair_price_total is not None:
        # Fair-price-based bands (tighter)
        if gap_pct < -0.05:
            label = 'BARGAIN'
        elif gap_pct < 0.05:
            label = 'AT_MARKET'
        elif gap_pct < 0.15:
            label = 'OVERPRICED'
        else:
            label = 'REJECT'
    else:
        # MoJ-only bands (legacy)
        if gap_pct < -0.10:
            label = 'BARGAIN'
        elif gap_pct < 0.10:
            label = 'AT_MARKET'
        elif gap_pct < 0.30:
            label = 'OVERPRICED'
        else:
            label = 'REJECT'

    return ListingComparison(
        listing_price=listing_price,
        listing_area_m2=listing_area_m2,
        moj_median_total=moj_total,
        benchmark_total=benchmark,
        benchmark_label=benchmark_label,
        gap_qar=gap,
        gap_pct=gap_pct,
        above_buyer_ceiling=above_buyer,
        above_market_ceiling=above_market,
        verdict_label=label,
    )


# ============================================================
# 6. DCF TEMPLATE BUILDER
# ============================================================

def build_dcf_template(property_report, area_name: str,
                       output_path: Path) -> Path:
    """
    Build a partially-filled deal_template.json for investment_model.py.

    Fills in what GIS knows; leaves user-specific fields (rents, financing) as
    null with TODO markers.
    """
    extent = getattr(property_report, 'extent', None)
    classification = getattr(property_report, 'classification', None)
    location = getattr(property_report, 'location', None)
    plot = getattr(property_report, 'plot', None)

    asset_type = classification.asset_type.value if classification else 'unknown'
    total_area = extent.total_area_m2 if extent else (plot.pdarea if plot else 0)

    template = {
        "_comment_purpose": (
            "Auto-generated by evaluate_property.py. "
            "Fill TODO_ fields, then run: python3 investment_model.py <this file>"
        ),
        "_gis_facts_locked": {
            "_note": "These fields were derived from Qatar GIS. Do not edit.",
            "asset_type": asset_type,
            "total_area_m2": round(total_area, 1) if total_area else None,
            "extent_pin_count": len(extent.included_pins) if extent else 1,
            "primary_pin": location.pin if location else None,
            "address_zone_street_building": (
                f"{location.zone}/{location.street}/{location.building}" if location else None
            ),
        },
        "deal": {
            "name": f"TODO_{area_name}_{asset_type}",
            "asset_type": asset_type,
            "location": area_name,
            "currency": "QAR",
            "analysis_date": None,
        },
        "purchase": {
            "price": None,
            "_TODO_price": "Asking price or expected purchase price",
            "transaction_costs_pct": 0.005,
        },
        "financing": {
            "type": "conventional",
            "down_payment_pct": 0.30,
            "loan_term_years": 15,
            "interest_rate": 0.055,
            "_TODO_interest": "Verify current QCB/bank rate; 5.5% is a 2026 placeholder",
            "amortization": "amortizing",
        },
        "operations": {
            "initial_gross_income_annual": None,
            "_TODO_income": (
                "Compute as: sum(unit_count × monthly_rent × 12) across categories. "
                f"Total area is {total_area:,.0f} m² — count units physically before estimating."
            ),
            "rent_growth_annual": 0.03,
            "opex_ratio": 0.23,
            "vacancy_allowance": 0.0,
            "income_breakdown": [
                {
                    "category": "TODO_category_name",
                    "count": None,
                    "monthly_rent": None,
                    "_TODO_count": "Verify from owner / municipal records, NOT visual inspection (≥30% error)",
                }
            ],
        },
        "capex_schedule": [
            {"year": 5, "amount": None, "_TODO_amount": "Mid-cycle major maintenance"},
            {"year": 8, "amount": None, "_TODO_amount": "HVAC + plumbing replacement"},
        ],
        "exit": {
            "holding_period_years": 10,
            "exit_cap_rate": 0.080,
            "selling_costs_pct": 0.025,
        },
        "discount_rate": 0.075,
        "sensitivity": {
            "rent_growth_range": [0.01, 0.02, 0.03, 0.04, 0.05],
            "exit_cap_range": [0.075, 0.080, 0.085, 0.090],
            "purchase_price_multipliers": [0.92, 0.96, 1.00, 1.04, 1.08],
        },
        "decision_thresholds": {
            "hurdle_rate": 0.075,
            "min_dscr": 1.25,
            "max_payback_years": 12,
        },
    }

    output_path = Path(output_path)
    output_path.write_text(json.dumps(template, ensure_ascii=False, indent=2),
                            encoding='utf-8')
    return output_path


# ============================================================
# 7. VERDICT ASSEMBLY
# ============================================================

def assemble_verdict(asset_type: str,
                      valuation: Optional[MoJValuation],
                      comparison: Optional[ListingComparison],
                      flags: Optional[ListingFlags],
                      requires_dcf: bool) -> tuple:
    """
    Returns (verdict, reasons, warnings).

    Verdict precedence:
      1. Excluding red flag → REJECT
      2. requires_dcf and no listing → DCF_REQUIRED
      3. Insufficient MoJ data → INSUFFICIENT_DATA
      4. Listing comparison → BARGAIN / INSPECT / REJECT
    """
    reasons = []
    warnings = []

    # Layer 1: red-flag exclusion
    if flags and flags.has_excluding_red_flag:
        excluders = [f['label'] for f in flags.red_flags if f['severity'] == 'exclude']
        return ('REJECT', [f'Excluded by red flag: {", ".join(excluders)}'], warnings)

    # Layer 2: requires DCF + no listing → ask for DCF
    if requires_dcf:
        if comparison is None:
            reasons.append(
                f'Asset type {asset_type} requires DCF analysis. '
                'No direct MoJ comparable exists for this property class.'
            )
            return ('DCF_REQUIRED', reasons, warnings)
        # If we have both DCF requirement AND a listing, we can do a sanity check
        # but the verdict still needs DCF
        warnings.append('Listing comparison is sanity-check only — final verdict needs DCF.')

    # Layer 3: insufficient MoJ
    if valuation is None or valuation.moj_median_total is None:
        reasons.append('No usable MoJ reference for this asset/area combination')
        return ('INSUFFICIENT_DATA', reasons, warnings)

    if valuation.bracket_reliable is False:
        warnings.append(
            f'Sample size {valuation.bracket_n} is below reliability threshold (n=10). '
            'Treat estimate as indicative only.'
        )

    # Layer 4: comparison-driven verdict
    if comparison is None:
        # No listing was provided — just report the MoJ-based estimate
        reasons.append(
            f'MoJ reference: median {valuation.moj_median_total:,.0f} QAR '
            f'(n={valuation.bracket_n})'
        )
        if flags and flags.green_flags:
            for g in flags.green_flags:
                warnings.append(f'Positive signal: {g["label"]}')
        return ('REFERENCE_ONLY', reasons, warnings)

    # Listing + MoJ both available
    if comparison.verdict_label == 'BARGAIN':
        verdict = 'BARGAIN'
        reasons.append(
            f'Listing {comparison.listing_price:,.0f} is {abs(comparison.gap_pct)*100:.1f}% '
            f'below {comparison.benchmark_label} ({comparison.benchmark_total:,.0f})'
        )
    elif comparison.verdict_label == 'AT_MARKET':
        verdict = 'INSPECT'
        reasons.append(f'Listing within fair-band of {comparison.benchmark_label} — fair price, inspect for value')
    elif comparison.verdict_label == 'OVERPRICED':
        verdict = 'INSPECT'
        reasons.append(
            f'Listing {comparison.gap_pct*100:.1f}% above {comparison.benchmark_label}. '
            f'Justification needed before proceeding.'
        )
        if comparison.above_buyer_ceiling:
            warnings.append(f'Listing exceeds buyer ceiling ({comparison.benchmark_label} +10%) — negotiate down')
    else:  # 'REJECT'
        verdict = 'REJECT'
        reasons.append(
            f'Listing {comparison.gap_pct*100:.1f}% above {comparison.benchmark_label} — beyond market acceptance'
        )

    # Add red-flag warnings (non-excluding)
    if flags:
        for f in flags.red_flags:
            if f['severity'] == 'warn':
                warnings.append(f'Caution: {f["label"]}')
        for g in flags.green_flags:
            warnings.append(f'Positive signal: {g["label"]}')

    return (verdict, reasons, warnings)


# ============================================================
# 8. MAIN PIPELINE
# ============================================================

def evaluate_property(zone: int, street: int, building: int,
                       moj_csv_path: Path,
                       area_name_in_moj: Optional[str] = None,
                       listing_price: Optional[float] = None,
                       listing_area_m2: Optional[float] = None,
                       listing_description: Optional[str] = None,
                       listing_bua_m2: Optional[float] = None,
                       bua_breakdown: Optional[BuaBreakdown] = None,
                       building_age_years: Optional[int] = None,
                       construction_tier: str = 'mid',
                       has_renovation: bool = False,
                       full_renovation: bool = False,
                       rental_income: Optional[float] = None,
                       potential_rental: Optional[float] = None,
                       opex_ratio: float = 0.23,
                       output_dir: Optional[Path] = None,
                       include_age: bool = False,
                       gis: Optional['QatarGIS'] = None) -> PropertyEvaluation:
    """
    End-to-end property evaluation.

    Steps:
      1. GIS lookup → asset type, extent, plot info
      2. MoJ reference loading or building
      3. MoJ strategy by asset type → moj_median
      3b. property_factors (if available) → adjustment → fair_price
      3c. Replacement cost (if BUA provided) → land + depreciated building
      3d. Blend MoJ + replacement cost → final reference value
      4. Listing comparison against blended value (or MoJ/replacement alone)
      5. Description analysis (if listing description provided)
      6. Verdict assembly
      7. DCF template generation (if applicable)

    New BUA parameters (v2):
      listing_bua_m2:      Total built-up area in m² (all floors incl. basement + annexes)
      building_age_years:  Override for building age (otherwise auto-detected from imagery)
      construction_tier:   'low' | 'mid' | 'high' — affects cost/m² estimate
      has_renovation:      Partial exterior/interior renovation done
      full_renovation:     Full renovation (interior + exterior + systems)
    """
    if not _MOJ_AVAILABLE:
        raise RuntimeError(
            'moj_reference module not available. Ensure moj_reference.py is on PYTHONPATH.'
        )

    # === Step 1: GIS lookup ===
    if gis is None:
        if not _GIS_AVAILABLE:
            raise RuntimeError(
                'qatar_gis module not available. Either install it on PYTHONPATH '
                'or pass an instance via the `gis` argument.'
            )
        gis = QatarGIS()
    report = gis.full_property_lookup(
        zone, street, building,
        include_imagery=False,  # imagery is optional; skip for speed
        output_dir=None,
    )

    if report is None:
        return PropertyEvaluation(
            address=f'{zone}/{street}/{building}',
            asset_type='unknown', classification_confidence='none',
            plot_area_m2=None, extent_total_m2=None,
            valuation=None, listing_comparison=None, listing_flags=None,
            requires_dcf=False, dcf_template_path=None,
            verdict='ADDRESS_NOT_FOUND',
            reasons=[f'No property at zone {zone}, street {street}, building {building}'],
            warnings=[], raw_property_report=None,
        )

    asset_type = report.classification.asset_type.value
    confidence = report.classification.confidence
    plot_area = report.plot.pdarea if report.plot else None
    extent_total = report.extent.total_area_m2 if report.extent else None

    # === Step 2: Load MoJ reference ===
    # We rebuild the reference for the area in question
    valuation = None
    moj_ref_dict = None
    trend_data = None
    resolved_area_warnings = []
    if asset_type in ASSET_TYPE_TO_MOJ_CATEGORY and ASSET_TYPE_TO_MOJ_CATEGORY[asset_type] is not None:
        try:
            import csv as _csv
            from datetime import datetime
            with open(moj_csv_path, 'r', encoding='utf-8-sig') as f:
                rows = list(_csv.DictReader(f))
            dates = []
            for r in rows:
                d = parse_date(r.get('تاريخ\xa0التثبيت', ''))
                if d: dates.append(d)
            max_d = max(dates) if dates else datetime.now()

            # Auto-resolve MoJ area name from GIS district if not provided
            if area_name_in_moj is None:
                district = getattr(report, 'district', None)
                if district is None:
                    raise ValueError(
                        'GIS returned no district for this address, and no '
                        'area_name_in_moj was provided. Cannot build MoJ reference.'
                    )
                resolved = resolve_moj_area_name(rows, district.aname)
                if resolved is None:
                    raise ValueError(
                        f'No matching MoJ area for GIS district "{district.aname}". '
                        f'Provide area_name_in_moj explicitly if MoJ uses a '
                        f'different spelling.'
                    )
                area_name_in_moj, n_transactions = resolved
                resolved_area_warnings.append(
                    f'GIS district: "{district.aname}". '
                    f'MoJ reference: "{area_name_in_moj}" (n={n_transactions} all-time).'
                )

            moj_ref_dict = build_reference(rows, area_name_in_moj, max_d)

            # === Step 2b: Compute price trend ===
            moj_category_for_trend = ASSET_TYPE_TO_MOJ_CATEGORY.get(asset_type, 'all')
            try:
                trend_data = compute_trend(rows, area_name_in_moj, max_d,
                                           category=moj_category_for_trend or 'all')
            except Exception:
                trend_data = None
        except Exception as e:
            return PropertyEvaluation(
                address=f'{zone}/{street}/{building}',
                asset_type=asset_type, classification_confidence=confidence,
                plot_area_m2=plot_area, extent_total_m2=extent_total,
                valuation=None, listing_comparison=None, listing_flags=None,
                requires_dcf=(asset_type in DCF_REQUIRED_TYPES),
                dcf_template_path=None,
                verdict='MOJ_LOAD_FAILED',
                reasons=[f'Could not load MoJ reference: {e}'],
                warnings=[], raw_property_report=None,
            )

    # === Step 3: Apply MoJ strategy ===
    if moj_ref_dict and plot_area:
        valuation = apply_moj_strategy(asset_type, plot_area, moj_ref_dict)

    # === Step 3b: Apply property_factors (NEW) ===
    # Compute objective GIS-driven adjustment to MoJ median, bounded to ±10%
    # per expert rule. This produces a "fair price" centered on MoJ but
    # adjusted for the property's actual measurable features.
    factors_warnings = []
    if valuation is not None and valuation.moj_median_total is not None and _FACTORS_AVAILABLE:
        try:
            # Get GPS coordinates from report
            lat_f = lon_f = None
            if report and hasattr(report, 'location') and report.location:
                loc = report.location
                if hasattr(loc, 'lat') and hasattr(loc, 'lon'):
                    lat_f, lon_f = loc.lat, loc.lon

            if lat_f is not None and lon_f is not None:
                # Build plot_shape from report if available
                shape_data = None
                if report and hasattr(report, 'plot') and report.plot:
                    ps = getattr(report.plot, 'shape', None)
                    if ps:
                        shape_data = {
                            'convex_hull_ratio': getattr(ps, 'convex_hull_ratio', None),
                            'vertex_count': getattr(ps, 'vertex_count', None),
                        }

                # Determine building age
                age_for_factors = building_age_years
                if age_for_factors is None and include_age and report:
                    try:
                        construction = report.construction
                        if construction and construction.earliest_built_year:
                            from datetime import datetime
                            age_for_factors = datetime.now().year - construction.earliest_built_year
                    except Exception:
                        pass

                factors_report = analyze_factors(
                    lat=lat_f, lon=lon_f,
                    purpose='residential',  # default; could be parameterized
                    plot_shape=shape_data,
                    building_age_years=age_for_factors,
                )

                adj = factors_report.adjustment
                fair_total = valuation.moj_median_total * (1 + adj)
                fair_per_m2 = (
                    valuation.moj_median_per_m2 * (1 + adj)
                    if valuation.moj_median_per_m2 else None
                )
                # Convert factors to plain dicts for serialization
                factors_detail = []
                for f in factors_report.factors:
                    factors_detail.append({
                        'code': f.name,
                        'label_ar': f.label_ar,
                        'label_en': f.name,
                        'direction': f.direction,
                        'weight': f.weight,
                        'distance_m': None,
                        'evidence': f.detail,
                        'source': f.source,
                    })
                valuation.factors_adjustment = adj
                valuation.fair_price_total = fair_total
                valuation.fair_price_per_m2 = fair_per_m2
                valuation.factors_detail = factors_detail
                if factors_report.notes:
                    factors_warnings.extend(factors_report.notes)
                if not factors_detail:
                    valuation.notes.append(
                        'لا توجد عوامل GIS ذات أثر — العقار في الفئة الأساسية. '
                        'السعر العادل = MoJ median.'
                    )
                else:
                    sign = '+' if adj >= 0 else ''
                    valuation.notes.append(
                        f'تعديل العوامل: {sign}{adj*100:.1f}% '
                        f'(من {len(factors_detail)} عامل)'
                    )
            else:
                factors_warnings.append('GPS coordinates unavailable — skipping property factors')
        except Exception as e:
            factors_warnings.append(f'تعذّر تحليل العوامل من GIS: {e}')

    # === Step 3c: Replacement cost (if BUA provided) ===
    replacement_cost_val = None
    blended_val = None
    has_bua = (bua_breakdown is not None) or (listing_bua_m2 is not None and listing_bua_m2 > 0)
    if has_bua and plot_area:
        # Determine building age: user override > imagery estimate > None
        age = building_age_years
        if age is None and include_age and report:
            try:
                construction = report.construction
                if construction and construction.earliest_built_year:
                    from datetime import datetime
                    age = datetime.now().year - construction.earliest_built_year
            except Exception:
                pass

        # Get MoJ land price for the same area
        moj_land_per_m2 = None
        if moj_ref_dict:
            land_data = _safe_get(moj_ref_dict, 'categories', 'land', default={})
            moj_land_per_m2 = _safe_get(land_data, 'price_per_m2', 'median')

        # Get municipality for calibrated costs
        muni_for_cost = None
        if moj_ref_dict:
            muni_for_cost = moj_ref_dict.get('municipality')

        replacement_cost_val = compute_replacement_cost(
            plot_area_m2=plot_area,
            moj_land_median_per_m2=moj_land_per_m2,
            building_age_years=age,
            construction_tier=construction_tier,
            has_renovation=has_renovation,
            full_renovation=full_renovation,
            municipality=muni_for_cost,
            bua_m2=listing_bua_m2,
            bua_breakdown=bua_breakdown,
        )

        effective_bua = replacement_cost_val.bua_m2

        # === Step 3d: Blend MoJ + replacement cost ===
        blended_val = blend_valuations(
            moj_val=valuation,
            repl_val=replacement_cost_val,
            bua_plot_ratio=replacement_cost_val.bua_plot_ratio,
            bracket_n=valuation.bracket_n if valuation else None,
        )

        if blended_val:
            factors_warnings.append(
                f'BUA {effective_bua:,.0f} م² → replacement cost '
                f'{replacement_cost_val.total_replacement_value:,.0f} QAR → '
                f'blended {blended_val.blended_value:,.0f} QAR '
                f'(MoJ {blended_val.moj_weight:.0%} / Repl {blended_val.replacement_weight:.0%})'
            )

    # === Step 4: Listing comparison ===
    # When blended valuation is available, override the MoJ median
    # in the comparison so the buyer ceiling is based on the blended number.
    comparison = None
    effective_valuation = valuation
    if blended_val and valuation:
        # Temporarily patch valuation's moj_median_total with the blended value
        # so compare_listing_to_moj uses it as the benchmark.
        from copy import deepcopy
        effective_valuation = deepcopy(valuation)
        effective_valuation.moj_median_total = blended_val.blended_value
        effective_valuation.notes.append(
            f'Benchmark overridden to blended value: {blended_val.blended_value:,.0f} QAR'
        )

    if listing_price is not None and effective_valuation is not None:
        comparison = compare_listing_to_moj(
            listing_price, listing_area_m2, effective_valuation, plot_area or 0
        )

    # === Step 5: Description analysis ===
    flags = analyze_listing_description(listing_description) if listing_description else None

    # === Step 6: Verdict ===
    requires_dcf = asset_type in DCF_REQUIRED_TYPES
    verdict, reasons, warnings = assemble_verdict(
        asset_type, valuation, comparison, flags, requires_dcf
    )

    # Add classification-level warnings
    if confidence == 'low':
        warnings.append(
            f'GIS classification confidence is LOW for {asset_type}. '
            'Manual verification recommended.'
        )

    # Surface area-resolution warnings (auto-resolved MoJ name from GIS district)
    for w in resolved_area_warnings:
        warnings.append(w)

    # Surface property_factors warnings
    for w in factors_warnings:
        warnings.append(w)

    # Add irregularity warnings from GIS
    if report.plot and report.plot.shape.irregularity_warning:
        warnings.append(f'Plot shape: {report.plot.shape.irregularity_warning}')

    # === Step 7: DCF template (if applicable) ===
    dcf_template_path = None
    if requires_dcf and output_dir is not None:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        addr_slug = f'{zone}_{street}_{building}'
        template_path = output_dir / f'{addr_slug}_deal_template.json'
        # Use GIS district name as the canonical location label for the template,
        # falling back to user-provided MoJ name, then to a generic placeholder.
        district_name = (
            getattr(getattr(report, 'district', None), 'aname', None)
            or area_name_in_moj
            or 'unknown_area'
        )
        build_dcf_template(report, district_name, template_path)
        dcf_template_path = str(template_path)
        warnings.append(f'DCF template generated → {template_path}')
        warnings.append('Fill TODO fields and run: python3 investment_model.py <template>')

    # Serialize property report for downstream tooling
    try:
        raw_report = {
            'asset_type': asset_type,
            'plot_area_m2': plot_area,
            'extent_total_m2': extent_total,
            'pin': report.location.pin if report.location else None,
            'gps': [report.location.lon, report.location.lat] if report.location else None,
            'classification_reasons': report.classification.reasons,
            'classification_flags': report.classification.flags,
        }
    except Exception:
        raw_report = None

    district = getattr(report, 'district', None)

    # === Step 7b: Rental analysis ===
    rental_result = None
    if rental_income is not None and rental_income > 0:
        # Determine property value for yield calculation
        prop_value = None
        if blended_val:
            prop_value = blended_val.blended_value
        elif valuation and valuation.fair_price_total:
            prop_value = valuation.fair_price_total
        elif valuation and valuation.moj_median_total:
            prop_value = valuation.moj_median_total

        if prop_value:
            # ── v2: extract BUA + area for itemized cost lookup ──
            bua_for_rental = None
            if bua_breakdown:
                bua_for_rental = bua_breakdown.total_bua
            elif listing_bua_m2:
                bua_for_rental = listing_bua_m2
            elif replacement_cost_val:
                bua_for_rental = replacement_cost_val.bua_m2

            # area name from GIS district (priority) or MoJ name (fallback)
            area_for_rental = None
            district_obj = getattr(report, 'district', None)
            if district_obj and district_obj.aname:
                area_for_rental = district_obj.aname
            elif area_name_in_moj:
                area_for_rental = area_name_in_moj

            # asset_type for service charge lookup
            sc_asset_type = 'apartment'
            if asset_type in ('STANDALONE_VILLA', 'standalone_villa'):
                sc_asset_type = 'villa_standalone'
            elif asset_type in ('COMPOUND_SMALL', 'COMPOUND_LARGE',
                                'compound_small', 'compound_large'):
                sc_asset_type = 'villa_compound'

            rental_result = compute_rental_analysis(
                rental_income_monthly=rental_income,
                property_value=prop_value,
                bua_m2=bua_for_rental,
                area=area_for_rental,
                precinct=None,  # TODO: extract from address when available
                building=None,
                asset_type=sc_asset_type,
                potential_monthly=potential_rental,
                listing_price=listing_price,
                # opex_ratio NOT passed → use itemized v2 calculation
            )

    # Build evaluation object first (confidence needs it)
    evaluation = PropertyEvaluation(
        address=f'{zone}/{street}/{building}',
        asset_type=asset_type,
        classification_confidence=confidence,
        plot_area_m2=plot_area,
        extent_total_m2=extent_total,
        gis_district_aname=district.aname if district else None,
        gis_district_ename=district.ename if district else None,
        gis_district_no=district.dist_no if district else None,
        moj_area_name=area_name_in_moj,
        valuation=valuation,
        replacement_cost=replacement_cost_val,
        blended=blended_val,
        listing_comparison=comparison,
        listing_flags=flags,
        requires_dcf=requires_dcf,
        dcf_template_path=dcf_template_path,
        trend=trend_data,
        rental_analysis=rental_result,
        valuation_date=datetime.now().strftime('%Y-%m-%d'),
        verdict=verdict,
        reasons=reasons,
        warnings=warnings,
        raw_property_report=raw_report,
    )

    # === Step 7c: Confidence score ===
    try:
        c_score, c_label, c_breakdown = compute_confidence(evaluation)
        evaluation.confidence_score = c_score
        evaluation.confidence_label = c_label
        evaluation.confidence_breakdown = c_breakdown
    except Exception:
        pass

    # === Step 7d (v2): Build reasoning_trace + market_position ===
    if _V2_MODULES_AVAILABLE:
        try:
            # Generate unique valuation ID for audit trail
            ts = datetime.now().strftime('%Y%m%d-%H%M%S')
            evaluation.valuation_id = f'THM-{ts}-{zone}{street}{building}'

            # Build the reasoning trace
            trace = ReasoningTrace(valuation_id=evaluation.valuation_id)

            # Identification step
            district_str = (district.aname if district else None) or area_name_in_moj or 'غير محدد'
            trace.add(
                category='identification',
                fact=(f'الأصل: {asset_type}، '
                      f'منطقة GIS: {district_str}، '
                      f'مساحة الأرض: {plot_area or "غير محدد"} م²'),
                source='gisqatar.org.qa',
                source_date=datetime.now().strftime('%Y-%m-%d'),
                confidence='high' if confidence == 'high' else 'medium',
            )
            trace.add_source('gisqatar.org.qa', 'https://services.gisqatar.org.qa')

            # MoJ + factors steps
            build_from_moj_valuation(trace, valuation)

            # Replacement cost step
            build_from_replacement_cost(trace, replacement_cost_val)

            # Blended valuation step
            if blended_val:
                trace.add(
                    category='valuation_synthesis',
                    fact=(f'دمج المقاربتين: MoJ={blended_val.moj_value:,.0f} '
                          f'(وزن {blended_val.moj_weight*100:.0f}%) + '
                          f'تكلفة={blended_val.replacement_value:,.0f} '
                          f'(وزن {blended_val.replacement_weight*100:.0f}%) → '
                          f'{blended_val.blended_value:,.0f}'),
                    source='internal_synthesis',
                    confidence='medium',
                    details={'moj_weight': blended_val.moj_weight,
                             'replacement_weight': blended_val.replacement_weight,
                             'reason': blended_val.blend_reason},
                )

            # Trend step
            if trend_data and trend_data.get('years'):
                slope = trend_data.get('slope_annual_pct', 0) * 100
                trace.add(
                    category='market_trend',
                    fact=f"اتجاه الأسعار: {slope:+.1f}%/سنة (آخر {len(trend_data['years'])} سنوات)",
                    source='data.gov.qa weekly bulletin (computed)',
                    confidence='medium',
                )

            # Listing comparison step
            build_from_listing_comparison(trace, comparison)

            # Listing flags step
            build_from_listing_flags(trace, flags)

            # Rental analysis step
            if rental_result:
                yield_pos = rental_result.get('yield_position_ar', '')
                if yield_pos:
                    trace.add(
                        category='income_analysis',
                        fact=yield_pos,
                        source='internal_yield_analysis_with_service_charges',
                        confidence='medium',
                        details={
                            'gross_yield': rental_result.get('on_valuation', {}).get('gross_yield_pct'),
                            'net_yield': rental_result.get('on_valuation', {}).get('net_yield_pct'),
                            'cost_breakdown': rental_result.get('cost_breakdown'),
                        },
                    )

            # Standard unknowns
            unknown_asset_type = 'apartment'
            if asset_type in ('STANDALONE_VILLA', 'standalone_villa'):
                unknown_asset_type = 'villa_standalone'
            elif asset_type in ('COMPOUND_SMALL', 'COMPOUND_LARGE'):
                unknown_asset_type = 'villa_compound'
            add_standard_unknowns(trace, asset_type=unknown_asset_type)

            evaluation.reasoning_trace = trace.to_dict()

            # ── Build market_position from listing comparison ──
            if comparison:
                listing_caveats = []
                if flags and flags.red_flags:
                    listing_caveats = [f['label'] for f in flags.red_flags]

                pos = market_position.compute_position(
                    listing_price=comparison.listing_price,
                    benchmark_price=comparison.benchmark_total,
                    benchmark_source=comparison.benchmark_label,
                    benchmark_n=valuation.bracket_n if valuation else None,
                    listing_caveats=listing_caveats,
                )
                evaluation.market_position = pos.to_dict()

        except Exception as e:
            # Never fail the evaluation just because trace building failed
            import sys
            print(f'[reasoning_trace warning] {e}', file=sys.stderr)

    return evaluation


# ============================================================
# 9. OUTPUT WRITERS
# ============================================================

def write_json(evaluation: PropertyEvaluation, path: Path) -> Path:
    """Write evaluation as JSON."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = asdict(evaluation)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    return path


# ============================================================
# 8. CONFIDENCE SCORE
# ============================================================

def compute_confidence(e: PropertyEvaluation) -> tuple:
    """
    Compute a confidence score (0-100) for the evaluation.

    Components:
        Sample size (0-35)     — how many comparable transactions
        Dispersion  (0-15)     — how tight the price range is
        BUA detail  (0-15)     — flat number vs full breakdown
        Building age (0-10)    — known vs unknown
        GIS factors (0-10)     — applied or not
        Trend data  (0-5)      — multi-year trend available
        Listing desc (0-5)     — description analyzed
        Listing price (0-5)    — comparison computed
    """
    score = 0
    breakdown = {}

    # 1. Sample size (0-35)
    n = 0
    if e.valuation:
        n = e.valuation.bracket_n or 0
    if n >= 20:
        s = 35
    elif n >= 10:
        s = 25
    elif n >= 5:
        s = 15
    else:
        s = 5
    breakdown['sample_size'] = {'score': s, 'max': 35, 'n': n}
    score += s

    # 2. Dispersion (0-15) — IQR / median
    s = 0
    if e.valuation and e.valuation.moj_median_total:
        low = e.valuation.estimated_value_low
        high = e.valuation.estimated_value_high
        med = e.valuation.moj_median_total
        if low and high and med > 0:
            iqr_ratio = (high - low) / med
            if iqr_ratio < 0.30:
                s = 15
            elif iqr_ratio < 0.50:
                s = 10
            elif iqr_ratio < 0.80:
                s = 7
            else:
                s = 3
        else:
            s = 5  # have median but no range
    breakdown['dispersion'] = {'score': s, 'max': 15}
    score += s

    # 3. BUA detail (0-15)
    if e.replacement_cost and e.replacement_cost.bua_breakdown:
        s = 15
        note = 'تفصيل كامل (5 مكونات)'
    elif e.replacement_cost:
        s = 8
        note = 'رقم مسطح'
    else:
        s = 0
        note = 'غير متوفر'
    breakdown['bua_detail'] = {'score': s, 'max': 15, 'note': note}
    score += s

    # 4. Building age (0-10)
    if e.replacement_cost and e.replacement_cost.building_age_years:
        s = 10
    else:
        s = 0
    breakdown['building_age'] = {'score': s, 'max': 10}
    score += s

    # 5. GIS factors (0-10)
    if e.valuation and e.valuation.factors_adjustment is not None:
        s = 10
    else:
        s = 0
    breakdown['gis_factors'] = {'score': s, 'max': 10}
    score += s

    # 6. Trend (0-5)
    if e.trend and len(e.trend.get('years', [])) >= 3:
        s = 5
    elif e.trend and len(e.trend.get('years', [])) >= 2:
        s = 3
    else:
        s = 0
    breakdown['trend'] = {'score': s, 'max': 5}
    score += s

    # 7. Listing description (0-5)
    if e.listing_flags:
        s = 5
    else:
        s = 0
    breakdown['listing_description'] = {'score': s, 'max': 5}
    score += s

    # 8. Listing price (0-5)
    if e.listing_comparison:
        s = 5
    else:
        s = 0
    breakdown['listing_price'] = {'score': s, 'max': 5}
    score += s

    # Label
    if score >= 80:
        label = 'ثقة عالية 🟢'
    elif score >= 60:
        label = 'ثقة متوسطة 🟡'
    elif score >= 40:
        label = 'ثقة منخفضة 🟠'
    else:
        label = 'إرشادي فقط 🔴'

    return score, label, breakdown


# ============================================================
# 9. RENTAL ANALYSIS
# ============================================================

def compute_rental_analysis(
    rental_income_monthly: float,
    property_value: float,
    bua_m2: Optional[float] = None,
    area: Optional[str] = None,
    precinct: Optional[str] = None,
    building: Optional[str] = None,
    asset_type: str = 'apartment',
    potential_monthly: Optional[float] = None,
    listing_price: Optional[float] = None,
    vacancy_pct: float = 0.085,           # ~شهر/سنة
    maintenance_pct_of_value: float = 0.005,  # 0.5% للمباني الجديدة
    management_pct: float = 0.0,          # 0% ذاتي، 5-8% بوكيل
    opex_ratio: Optional[float] = None,   # backward compat — إن مُرّر استخدمه
) -> dict:
    """
    حساب العائد بتكاليف مفصّلة (Thammen v2).

    التغيير عن v1:
      v1: opex_ratio=0.23 مسطح → غير دقيق وغير شفاف
      v2: تكاليف مفصّلة:
        - رسوم الخدمات (من service_charge_db بحسب البرج/المنطقة)
        - شغور (افتراض 8.5% = شهر/سنة)
        - صيانة (0.5% من القيمة سنوياً للمباني الجديدة)
        - إدارة (0% للذاتي، 5-8% بوكيل)

    Args:
        rental_income_monthly: الإيجار الشهري المؤكَّد
        property_value: القيمة المُستخدَمة في الحساب
        bua_m2: المساحة المبنية (لازمة لحساب رسوم الخدمات per-m2)
        area, precinct, building: للبحث في service_charge_db
        asset_type: 'apartment' / 'villa_standalone' / 'villa_compound'
        potential_monthly: الإيجار المحتمل (إن لم يكن العقار مؤجَّراً بالكامل)
        listing_price: سعر الإعلان (للمقارنة)
        vacancy_pct: نسبة الشغور المُقدَّرة (افتراض 8.5%)
        maintenance_pct_of_value: نسبة الصيانة من قيمة العقار (افتراض 0.5%)
        management_pct: نسبة إدارة الإيجار (افتراض 0% للإدارة الذاتية)
        opex_ratio: للتوافق مع v1 — إن مُرّر استُخدم بدل التفصيل

    Returns:
        dict بـ:
          - الإيجار الإجمالي والصافي
          - تفصيل التكاليف (مهم!)
          - العائد الإجمالي والصافي
          - موضع العائد مقابل السوق القطري (5-6% طبيعي)
          - حساسية: تأثير ارتفاع رسوم الخدمات أو الشغور
    """
    annual_gross = rental_income_monthly * 12

    # ── حساب التكاليف المفصّلة ──
    cost_breakdown = {
        'service_charge_annual': 0.0,
        'service_charge_source': '',
        'service_charge_confidence': '',
        'vacancy_provision': 0.0,
        'maintenance_provision': 0.0,
        'management_fee': 0.0,
    }

    # 1. رسوم الخدمات — من service_charge_db
    if _V2_MODULES_AVAILABLE and bua_m2 and bua_m2 > 0:
        sc_record = service_charge_db.lookup(
            area=area, precinct=precinct, building=building,
            asset_type=asset_type
        )
        sc_annual = sc_record.annual_total(bua_m2) or 0.0
        cost_breakdown['service_charge_annual'] = round(sc_annual)
        cost_breakdown['service_charge_per_m2_monthly'] = sc_record.monthly_per_m2
        cost_breakdown['service_charge_source'] = sc_record.source
        cost_breakdown['service_charge_confidence'] = sc_record.confidence
        cost_breakdown['service_charge_notes'] = sc_record.notes

    # 2. الشغور
    cost_breakdown['vacancy_provision'] = round(annual_gross * vacancy_pct)
    cost_breakdown['vacancy_pct_used'] = vacancy_pct

    # 3. الصيانة
    if property_value and property_value > 0:
        cost_breakdown['maintenance_provision'] = round(property_value * maintenance_pct_of_value)
        cost_breakdown['maintenance_pct_of_value_used'] = maintenance_pct_of_value

    # 4. الإدارة
    cost_breakdown['management_fee'] = round(annual_gross * management_pct)
    cost_breakdown['management_pct_used'] = management_pct

    total_costs = sum([
        cost_breakdown['service_charge_annual'],
        cost_breakdown['vacancy_provision'],
        cost_breakdown['maintenance_provision'],
        cost_breakdown['management_fee'],
    ])

    # ── دعم backward compat: إن مُرّر opex_ratio استخدمه ──
    if opex_ratio is not None:
        annual_net = annual_gross * (1 - opex_ratio)
        total_costs = annual_gross - annual_net
        cost_breakdown['legacy_opex_ratio_used'] = opex_ratio
        cost_breakdown['legacy_warning'] = (
            'opex_ratio مسطح يُستخدم بدلاً من التفصيل — أقل دقة. '
            'حدّد bua_m2 و area للحصول على تفصيل حقيقي.'
        )
    else:
        annual_net = annual_gross - total_costs

    result = {
        'current_monthly': rental_income_monthly,
        'annual_gross': round(annual_gross),
        'annual_net': round(annual_net),
        'total_annual_costs': round(total_costs),
        'cost_breakdown': cost_breakdown,
        'cost_breakdown_pct_of_rent': {
            'service_charge_pct': round(cost_breakdown['service_charge_annual'] / annual_gross * 100, 1) if annual_gross else 0,
            'vacancy_pct': round(cost_breakdown['vacancy_provision'] / annual_gross * 100, 1) if annual_gross else 0,
            'maintenance_pct': round(cost_breakdown['maintenance_provision'] / annual_gross * 100, 1) if annual_gross else 0,
            'management_pct': round(cost_breakdown['management_fee'] / annual_gross * 100, 1) if annual_gross else 0,
        },
    }

    # Yield on valuation
    if property_value and property_value > 0:
        gross_yield = annual_gross / property_value
        net_yield = annual_net / property_value
        payback = property_value / annual_net if annual_net > 0 else None
        result['on_valuation'] = {
            'gross_yield_pct': round(gross_yield * 100, 2),
            'net_yield_pct': round(net_yield * 100, 2),
            'payback_years': round(payback, 1) if payback else None,
        }

    # Yield on listing price (if available)
    if listing_price and listing_price > 0:
        gross_yield_l = annual_gross / listing_price
        net_yield_l = annual_net / listing_price
        payback_l = listing_price / annual_net if annual_net > 0 else None
        result['on_listing_price'] = {
            'gross_yield_pct': round(gross_yield_l * 100, 2),
            'net_yield_pct': round(net_yield_l * 100, 2),
            'payback_years': round(payback_l, 1) if payback_l else None,
        }

    # Potential (if all units rented)
    if potential_monthly and potential_monthly > rental_income_monthly:
        pot_annual = potential_monthly * 12
        # نطبّق نفس تفصيل التكاليف على الإيجار المحتمل
        pot_costs = (cost_breakdown['service_charge_annual']
                     + pot_annual * vacancy_pct
                     + cost_breakdown['maintenance_provision']
                     + pot_annual * management_pct)
        pot_net = pot_annual - pot_costs
        result['potential'] = {
            'monthly': potential_monthly,
            'annual_gross': round(pot_annual),
            'annual_net': round(pot_net),
        }
        if property_value and property_value > 0:
            result['potential']['gross_yield_pct'] = round(pot_annual / property_value * 100, 2)
            result['potential']['net_yield_pct'] = round(pot_net / property_value * 100, 2)

    # ── الموضع مقابل السوق القطري (وصفي، ليس توصية) ──
    # قاعدة قطر: 5-6% صافي طبيعي، أكثر من 6% فوق المتوسط، أقل من 4% تحت المتوسط
    primary_yield = result.get('on_valuation', {}).get('net_yield_pct', 0)
    result['qatar_market_normal_band'] = (5.0, 6.0)
    if primary_yield >= 6.0:
        position = 'above_market'
        position_ar = (f'العائد {primary_yield:.2f}% فوق متوسط السوق القطري (5-6%). '
                       f'فحص أسباب الارتفاع: بناء مرتفع جداً، أو إيجار غير مستدام، '
                       f'أو لقطة فعلية. يستحق التحقق التفصيلي.')
    elif primary_yield >= 5.0:
        position = 'at_market_upper'
        position_ar = (f'العائد {primary_yield:.2f}% ضمن المتوسط الأعلى للسوق القطري (5-6%). '
                       f'استثمار طبيعي.')
    elif primary_yield >= 4.0:
        position = 'at_market_lower'
        position_ar = (f'العائد {primary_yield:.2f}% أقل من متوسط السوق القطري بقليل. '
                       f'مناسب كسكن مع دخل، ضعيف كاستثمار صرف. تحقق من إمكانية رفع الإيجار.')
    elif primary_yield >= 2.0:
        position = 'below_market'
        position_ar = (f'العائد {primary_yield:.2f}% أقل بشكل ملحوظ من متوسط السوق. '
                       f'الأسباب الشائعة: شراء بسعر مرتفع، إيجار منخفض، رسوم خدمات مرتفعة.')
    else:
        position = 'far_below_market'
        position_ar = (f'العائد {primary_yield:.2f}% ضعيف جداً مقارنة بمتوسط السوق. '
                       f'غير مجدٍ كاستثمار صافٍ، إلا إذا كان الهدف هو الاستخدام الشخصي.')

    result['yield_position'] = position
    result['yield_position_ar'] = position_ar

    # ── حساسية ──
    if property_value and property_value > 0 and cost_breakdown['service_charge_annual'] > 0:
        # ماذا لو ارتفعت رسوم الخدمات 20%
        sc_higher = cost_breakdown['service_charge_annual'] * 1.20
        net_sensitive_sc = (annual_gross - cost_breakdown['vacancy_provision']
                            - sc_higher - cost_breakdown['maintenance_provision']
                            - cost_breakdown['management_fee'])
        # ماذا لو انخفض الإيجار 10%
        rent_lower = annual_gross * 0.90
        net_sensitive_rent = (rent_lower - rent_lower * vacancy_pct
                              - cost_breakdown['service_charge_annual']
                              - cost_breakdown['maintenance_provision']
                              - rent_lower * management_pct)
        result['sensitivity'] = {
            'if_service_charge_up_20pct': {
                'net_yield_pct': round(net_sensitive_sc / property_value * 100, 2),
                'change_bp': round((net_sensitive_sc - annual_net) / property_value * 10000),
            },
            'if_rent_down_10pct': {
                'net_yield_pct': round(net_sensitive_rent / property_value * 100, 2),
                'change_bp': round((net_sensitive_rent - annual_net) / property_value * 10000),
            },
        }

    # ── backward compat: حقل verdict_ar إذا كان موجوداً ──
    # نعيد استخدامه كـ position_ar لكن نتركه بنفس المفتاح للتوافق
    result['verdict_ar'] = position_ar  # للـ frontend القديم
    result['_v2_notice'] = (
        'حقول جديدة في v2: cost_breakdown، yield_position، sensitivity. '
        'حقل verdict_ar محتفظ به للتوافق لكنه الآن وصفي لا توصوي.'
    )

    return result


# ============================================================
# 9b. SETBACK-BASED FOOTPRINT CALCULATION
# ============================================================

def compute_max_footprint(plot_polygon_4326: list, plot_area_m2: float) -> Optional[dict]:
    """
    Calculate maximum buildable footprint from plot dimensions and setback rules.

    Qatar Municipality residential setbacks:
      Front: 5m, Sides: 3m each, Back: 3m

    Returns:
        {max_footprint_m2, coverage_pct, plot_width, plot_depth}
    """
    if not plot_polygon_4326 or len(plot_polygon_4326) < 3:
        return None

    try:
        import math
        # Compute bounding box dimensions in meters
        lons = [p[0] for p in plot_polygon_4326]
        lats = [p[1] for p in plot_polygon_4326]

        # Convert to approximate meters
        mid_lat = sum(lats) / len(lats)
        m_per_deg_lat = 111320
        m_per_deg_lon = 111320 * math.cos(math.radians(mid_lat))

        width_m = (max(lons) - min(lons)) * m_per_deg_lon
        depth_m = (max(lats) - min(lats)) * m_per_deg_lat

        # Ensure width < depth (width = short side)
        if width_m > depth_m:
            width_m, depth_m = depth_m, width_m

        buildable_w = max(0, width_m - SETBACK_SIDE * 2)
        buildable_d = max(0, depth_m - SETBACK_FRONT - SETBACK_BACK)
        footprint = buildable_w * buildable_d
        coverage = footprint / plot_area_m2 if plot_area_m2 > 0 else 0

        return {
            'plot_width_m': round(width_m, 1),
            'plot_depth_m': round(depth_m, 1),
            'buildable_width_m': round(buildable_w, 1),
            'buildable_depth_m': round(buildable_d, 1),
            'max_footprint_m2': round(footprint),
            'max_coverage_pct': round(coverage * 100, 1),
        }
    except Exception:
        return None


# ============================================================
# 9c. BUA ESTIMATION FROM SATELLITE
# ============================================================

def estimate_footprint_from_imagery(
    polygon_4326: list,
    year: int = 2024,
    threshold: int = 140,
    pixel_res: float = 0.265,
) -> Optional[dict]:
    """
    Estimate building footprint area from satellite imagery.

    Method: threshold on grayscale intensity within the plot polygon.
    Dark pixels = building/structure, light pixels = open ground/garden.

    Args:
        polygon_4326: list of (lon, lat) tuples defining the plot
        year: imagery year to use
        threshold: pixel intensity below this = building (0-255)
        pixel_res: meters per pixel (LOD10 = 0.265)

    Returns:
        {
            'footprint_m2': float,     # estimated building footprint
            'open_area_m2': float,     # open ground
            'coverage_pct': float,     # footprint / total
            'estimated_bua_1floor': float,
            'estimated_bua_2floor': float,
            'note': str,
        }
    """
    try:
        from PIL import Image, ImageDraw
        import urllib.request
        import math
    except ImportError:
        return None

    if not polygon_4326 or len(polygon_4326) < 3:
        return None

    # Get bounding box
    lons = [p[0] for p in polygon_4326]
    lats = [p[1] for p in polygon_4326]
    min_lon, max_lon = min(lons), max(lons)
    min_lat, max_lat = min(lats), max(lats)

    try:
        from qatar_gis import QatarGIS
        import tempfile, os
        gis = QatarGIS(verbose=False)

        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
            tmp_path = f.name

        gis.render_overlay(
            [polygon_4326], tmp_path,
            year=year, target_res=pixel_res,
            padding_tiles=0,
        )

        img = Image.open(tmp_path)
        w, h = img.size

        # Build a mask for pixels INSIDE the polygon only
        # Convert polygon GPS to pixel coordinates
        # pixel_x = (lon - min_lon_of_image) / lon_per_pixel
        # We need the image's geo extent — approximate from bbox + padding
        img_min_lon = min_lon - (max_lon - min_lon) * 0.15
        img_max_lon = max_lon + (max_lon - min_lon) * 0.15
        img_min_lat = min_lat - (max_lat - min_lat) * 0.15
        img_max_lat = max_lat + (max_lat - min_lat) * 0.15

        lon_per_px = (img_max_lon - img_min_lon) / w
        lat_per_px = (img_max_lat - img_min_lat) / h

        poly_pixels = []
        for lon, lat in polygon_4326:
            px = int((lon - img_min_lon) / lon_per_px)
            py = int((img_max_lat - lat) / lat_per_px)  # y is inverted
            poly_pixels.append((px, py))

        # Create mask
        mask = Image.new('L', (w, h), 0)
        ImageDraw.Draw(mask).polygon(poly_pixels, fill=255)

        # Apply mask: only count pixels inside polygon
        gray = img.convert('L')
        pixels_in_polygon = []
        mask_data = list(mask.getdata())
        gray_data = list(gray.getdata())
        for i in range(len(mask_data)):
            if mask_data[i] > 0:
                pixels_in_polygon.append(gray_data[i])

        total_inside = len(pixels_in_polygon)
        dark = sum(1 for p in pixels_in_polygon if p < threshold)
        light = total_inside - dark

        pixel_area = pixel_res ** 2
        footprint = dark * pixel_area
        open_area = light * pixel_area
        total_area = total_inside * pixel_area
        coverage = dark / total_inside if total_inside > 0 else 0

        os.unlink(tmp_path)

        return {
            'footprint_m2': round(footprint),
            'open_area_m2': round(open_area),
            'total_pixel_area_m2': round(total_area),
            'coverage_pct': round(coverage * 100, 1),
            'estimated_bua_1floor': round(footprint),
            'estimated_bua_2floor': round(footprint * 2),
            'estimated_bua_3floor': round(footprint * 3),
            'threshold': threshold,
            'pixel_res': pixel_res,
            'note': 'تقدير أولي — دقة ±25%. عدّل يدوياً إذا تختلف.',
        }
    except Exception as e:
        return {'error': str(e)}


def print_evaluation(evaluation: PropertyEvaluation):
    """Console-friendly summary."""
    e = evaluation
    print(f'\n{"="*70}')
    print(f'  Property Evaluation: {e.address}')
    print(f'{"="*70}')
    print(f'  Asset type:       {e.asset_type} (confidence: {e.classification_confidence})')
    if e.plot_area_m2:
        print(f'  Plot area:        {e.plot_area_m2:,.0f} m²')
    if e.extent_total_m2 and e.extent_total_m2 != e.plot_area_m2:
        print(f'  Extent total:     {e.extent_total_m2:,.0f} m² (multi-parcel)')

    if e.valuation:
        print(f'\n  [MoJ Valuation]')
        print(f'    Strategy:       {e.valuation.strategy}')
        if e.valuation.moj_median_total:
            print(f'    MoJ median:     {e.valuation.moj_median_total:,.0f} QAR')
        if e.valuation.estimated_value_low and e.valuation.estimated_value_high:
            print(f'    Value range:    {e.valuation.estimated_value_low:,.0f} – '
                  f'{e.valuation.estimated_value_high:,.0f} QAR')
        # Show fair price layer if available
        if e.valuation.fair_price_total is not None:
            adj = e.valuation.factors_adjustment
            sign = '+' if adj >= 0 else ''
            print(f'\n  [GIS Factors → Fair Price]')
            print(f'    Adjustment:     {sign}{adj*100:.1f}% (capped to ±10%)')
            print(f'    Fair price:     {e.valuation.fair_price_total:,.0f} QAR')
            if e.valuation.factors_detail:
                for f in e.valuation.factors_detail:
                    s = '+' if f['direction'] == 'positive' else '−'
                    icon = '✚' if f['direction'] == 'positive' else '✖'
                    print(f'    {icon}  {f["label_ar"]}  ({s}{abs(f["weight"]):.3f})')
            else:
                print(f'    (لا توجد عوامل GIS ذات أثر)')
        for n in e.valuation.notes:
            print(f'    • {n}')

    if e.replacement_cost:
        rc = e.replacement_cost
        print(f'\n  [Replacement Cost (BUA = {rc.bua_m2:,.0f} m²)]')
        print(f'    BUA/plot ratio: {rc.bua_plot_ratio:.2f}')
        print(f'    Land value:     {rc.land_value:,.0f} QAR ({rc.land_price_per_m2:,.0f}/m²)')
        if rc.component_costs:
            print(f'    Building (component breakdown):')
            for c in rc.component_costs:
                print(f'      {c["component"]:25s}  {c["area_m2"]:>6,.0f} m² × {c["cost_per_m2"]:>5,}/m² = {c["subtotal"]:>10,} QAR')
            print(f'      {"─" * 55}')
            print(f'      {"Total new":25s}  {rc.bua_m2:>6,.0f} m²              = {rc.construction_cost_new:>10,} QAR')
        else:
            print(f'    Building new:   {rc.construction_cost_new:,.0f} QAR')
        if rc.building_age_years:
            print(f'    Age/deprec:     {rc.building_age_years}y → -{rc.depreciation_pct*100:.0f}%'
                  f' + recovery {rc.renovation_recovery_pct*100:.0f}%')
        print(f'    Building depr:  {rc.depreciated_building_value:,.0f} QAR')
        print(f'    ─────────────')
        print(f'    Total:          {rc.total_replacement_value:,.0f} QAR')
        for n in rc.notes:
            print(f'    • {n}')

    if e.blended:
        b = e.blended
        print(f'\n  [Blended Valuation]')
        print(f'    MoJ ({b.moj_weight:.0%}):      {b.moj_value:,.0f} QAR' if b.moj_value else '')
        print(f'    Repl ({b.replacement_weight:.0%}):     {b.replacement_value:,.0f} QAR' if b.replacement_value else '')
        print(f'    ═══════════════')
        print(f'    Blended:        {b.blended_value:,.0f} QAR')
        if b.blended_low and b.blended_high:
            print(f'    Range:          {b.blended_low:,.0f} – {b.blended_high:,.0f} QAR')
        print(f'    Reason:         {b.blend_reason}')
        for n in b.notes:
            print(f'    • {n}')

    if e.listing_comparison:
        c = e.listing_comparison
        print(f'\n  [Listing vs Benchmark]')

    if e.trend:
        t = e.trend
        icon = '📈' if t['label'] == 'ارتفاع' else ('📉' if t['label'] == 'انخفاض' else '➡️')
        print(f'\n  [Price Trend — {t["category"]}]')
        print(f'    Direction:      {icon} {t["label"]} ({t["slope_annual_pct"]*100:+.1f}%/year)')
        if t.get('latest_vs_peak_pct') and t['latest_vs_peak_pct'] < -0.05:
            print(f'    vs Peak:        {t["latest_vs_peak_pct"]*100:.1f}% from peak')
        for y in t.get('years', []):
            bar = '█' * max(1, int(y['median_ft'] / 30))
            print(f'    {y["year"]}  {bar} {y["median_ft"]:>4} QAR/ft²  (n={y["n"]})')

    if e.listing_comparison:
        print(f'    Listing:        {c.listing_price:,.0f} QAR')
        print(f'    Benchmark:      {c.benchmark_total:,.0f} QAR ({c.benchmark_label})')
        if c.benchmark_total != c.moj_median_total:
            print(f'      (MoJ median was: {c.moj_median_total:,.0f} QAR)')
        sign = '+' if c.gap_qar >= 0 else ''
        print(f'    Gap:            {sign}{c.gap_qar:,.0f} QAR ({sign}{c.gap_pct*100:.1f}%)')
        print(f'    Verdict label:  {c.verdict_label}')

    if e.listing_flags:
        if e.listing_flags.red_flags:
            print(f'\n  [Red Flags]')
            for f in e.listing_flags.red_flags:
                marker = '🚫' if f['severity'] == 'exclude' else '⚠️'
                print(f'    {marker}  {f["label"]}')
        if e.listing_flags.green_flags:
            print(f'\n  [Green Flags]')
            for g in e.listing_flags.green_flags:
                print(f'    ✓  {g["label"]}')

    if e.rental_analysis:
        ra = e.rental_analysis
        print(f'\n  [Rental Analysis]')
        print(f'    Monthly income:   {ra["current_monthly"]:,.0f} QAR')
        on_val = ra.get('on_valuation', {})
        if on_val:
            print(f'    Gross yield:      {on_val["gross_yield_pct"]:.1f}% (on valuation)')
            print(f'    Net yield:        {on_val["net_yield_pct"]:.1f}% (after {ra["opex_ratio"]*100:.0f}% opex)')
            if on_val.get('payback_years'):
                print(f'    Payback:          {on_val["payback_years"]:.0f} years')
        on_list = ra.get('on_listing_price', {})
        if on_list:
            print(f'    Net yield (list): {on_list["net_yield_pct"]:.1f}% (on listing price)')
        pot = ra.get('potential', {})
        if pot:
            print(f'    Potential yield:   {pot.get("net_yield_pct",0):.1f}% (if fully rented @ {pot["monthly"]:,.0f}/mo)')
        print(f'    → {ra["verdict_ar"]}')

    if e.confidence_score is not None:
        print(f'\n  [Confidence: {e.confidence_score}/100 — {e.confidence_label}]')
        if e.confidence_breakdown:
            for key, item in e.confidence_breakdown.items():
                bar = '█' * item['score'] + '░' * (item['max'] - item['score'])
                print(f'    {bar} {item["score"]:>2}/{item["max"]:>2}  {key}')

    print(f'\n  ━━━ VERDICT: {e.verdict} ━━━')
    for r in e.reasons:
        print(f'    • {r}')
    if e.warnings:
        print(f'\n  Warnings:')
        for w in e.warnings:
            print(f'    ⚠ {w}')
    if e.dcf_template_path:
        print(f'\n  DCF template: {e.dcf_template_path}')
    print()


# ============================================================
# 10. CLI
# ============================================================

def main():
    p = argparse.ArgumentParser(description='Unified Qatari property evaluator')
    p.add_argument('zone', type=int)
    p.add_argument('street', type=int)
    p.add_argument('building', type=int)
    p.add_argument('--moj-csv', type=Path, required=True,
                   help='Path to MoJ weekly-real-estates-sales-bulletin CSV')
    p.add_argument('--area-name', required=False, default=None,
                   help='MoJ area name (optional — auto-resolved from GIS district if omitted). '
                        'See system prompt §3 for naming convention.')
    p.add_argument('--listing-price', type=float)
    p.add_argument('--listing-area', type=float)
    p.add_argument('--listing-description', type=str)
    p.add_argument('--listing-bua', type=float,
                   help='Total built-up area in m² (flat, no breakdown)')
    p.add_argument('--main-footprint', type=float, default=0,
                   help='Ground-floor footprint of main building (m²)')
    p.add_argument('--basement-area', type=float, default=0,
                   help='Basement area (m²)')
    p.add_argument('--upper-floors-area', type=float, default=0,
                   help='Total area of upper floors above ground (m²)')
    p.add_argument('--upper-floor-count', type=int, default=0,
                   help='Number of upper floors')
    p.add_argument('--annexes-area', type=float, default=0,
                   help='Total area of all annexes (single-story)')
    p.add_argument('--annex-count', type=int, default=0,
                   help='Number of annexes')
    p.add_argument('--external-area', type=float, default=0,
                   help='External structures area (مجلس/مطبخ خارجي)')
    p.add_argument('--building-age', type=int,
                   help='Building age in years (overrides imagery estimate)')
    p.add_argument('--construction-tier', choices=['low', 'mid', 'high'], default='mid',
                   help='Construction quality tier for replacement cost (default: mid)')
    p.add_argument('--has-renovation', action='store_true',
                   help='Partial renovation done (exterior/cosmetic)')
    p.add_argument('--full-renovation', action='store_true',
                   help='Full renovation done (interior + exterior + systems)')
    p.add_argument('--rental-income', type=float, default=None,
                   help='Current confirmed monthly rental income (QAR)')
    p.add_argument('--potential-rental', type=float, default=None,
                   help='Potential monthly income if all units rented (QAR)')
    p.add_argument('--opex-ratio', type=float, default=0.23,
                   help='Operating expense ratio (default: 0.23 = 23%%)')
    p.add_argument('--include-age', action='store_true',
                   help='Estimate construction age from historical imagery (slow, ~30-60s)')
    p.add_argument('--output-dir', type=Path, default=Path('./eval_output'))
    p.add_argument('--quiet', action='store_true', help='Suppress console output')
    args = p.parse_args()

    # Build BUA breakdown if any component is specified
    breakdown = None
    if any([args.main_footprint, args.basement_area, args.upper_floors_area,
            args.annexes_area, args.external_area]):
        breakdown = BuaBreakdown(
            main_footprint_m2=args.main_footprint,
            basement_m2=args.basement_area,
            upper_floors_m2=args.upper_floors_area,
            upper_floor_count=args.upper_floor_count,
            annexes_m2=args.annexes_area,
            annex_count=args.annex_count,
            external_m2=args.external_area,
        )

    evaluation = evaluate_property(
        zone=args.zone, street=args.street, building=args.building,
        moj_csv_path=args.moj_csv,
        area_name_in_moj=args.area_name,
        listing_price=args.listing_price,
        listing_area_m2=args.listing_area,
        listing_description=args.listing_description,
        listing_bua_m2=args.listing_bua,
        bua_breakdown=breakdown,
        building_age_years=args.building_age,
        construction_tier=args.construction_tier,
        has_renovation=args.has_renovation,
        full_renovation=args.full_renovation,
        rental_income=args.rental_income,
        potential_rental=args.potential_rental,
        opex_ratio=args.opex_ratio,
        include_age=args.include_age,
        output_dir=args.output_dir,
    )

    addr_slug = f'{args.zone}_{args.street}_{args.building}'
    json_path = args.output_dir / f'{addr_slug}_evaluation.json'
    write_json(evaluation, json_path)

    if not args.quiet:
        print_evaluation(evaluation)
        print(f'  JSON saved → {json_path}')


if __name__ == '__main__':
    main()

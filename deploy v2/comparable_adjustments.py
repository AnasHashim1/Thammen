#!/usr/bin/env python3
"""
comparable_adjustments.py — Individual comparable transaction adjustments.

RICS Red Book VPS 4 §7 requires each comparable transaction to be adjusted
individually for: time, location, size, condition, and terms.

Our approach:
    1. Time adjustment:  monthly rate derived from area price trend
    2. Size adjustment:  per-ft² premium/discount by bracket
    3. Location sub-adj: GIS proximity factors (if available)
    4. Condition caveat:  MoJ has no condition data — explicit unknown

This produces an "adjusted median" that is defensible under RICS,
unlike a raw median which ignores transaction-specific differences.

Usage:
    from comparable_adjustments import adjust_comparables, AdjustedResult

    result = adjust_comparables(
        transactions=[...],          # raw MoJ transactions
        target_area_m2=542,          # subject property size
        target_date=datetime.now(),  # valuation date
        trend_slope_annual=-3.4,     # % annual price change
    )
    print(result.adjusted_median)
    print(result.adjustment_table)   # per-transaction adjustments (RICS-style)
"""

import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, List, Dict

# ============================================================
# CONSTANTS
# ============================================================

# Size brackets and their relative per-ft² pricing
# Derived empirically: smaller plots have higher per-ft² prices
SIZE_BRACKET_ADJUSTMENT = {
    # (lo, hi): multiplier relative to 400-600 bracket (=1.0)
    (0, 400):      1.10,   # small plots: +10% per ft²
    (400, 600):    1.00,   # reference bracket
    (600, 900):    0.95,   # moderate: -5%
    (900, 1500):   0.90,   # large: -10%
    (1500, 99999): 0.82,   # very large: -18%
}


@dataclass
class TransactionAdjustment:
    """One comparable transaction with all adjustments applied."""
    # Original data
    date: Optional[str]
    area_m2: float
    total_price: float
    price_per_m2: float

    # Adjustments (multiplicative)
    time_adj_pct: float = 0.0
    size_adj_pct: float = 0.0
    location_adj_pct: float = 0.0  # reserved for GIS sub-location

    # Adjusted values
    adjusted_price_per_m2: float = 0.0
    adjusted_total: float = 0.0

    # Meta
    adjustment_notes: List[str] = field(default_factory=list)

    @property
    def total_adj_pct(self):
        return self.time_adj_pct + self.size_adj_pct + self.location_adj_pct


@dataclass
class AdjustedResult:
    """Result of adjusting a set of comparables."""
    raw_median_per_m2: float
    adjusted_median_per_m2: float
    adjusted_median_total: float            # at target size
    adjusted_low: float                     # p25
    adjusted_high: float                    # p75
    n: int
    target_area_m2: float
    trend_used_pct: Optional[float]         # annual % used
    adjustment_table: List[TransactionAdjustment]
    method_note: str
    caveats: List[str] = field(default_factory=list)


def _bracket_for(area_m2):
    for (lo, hi), mult in SIZE_BRACKET_ADJUSTMENT.items():
        if lo <= area_m2 < hi:
            return (lo, hi), mult
    return (1500, 99999), 0.82


def adjust_comparables(
    transactions: List[dict],
    target_area_m2: float,
    target_date: datetime = None,
    trend_slope_annual: float = 0.0,
    location_adj_pct: float = 0.0,
) -> Optional[AdjustedResult]:
    """
    Adjust each comparable transaction to the subject property.

    Each transaction dict must have:
        date (str YYYY-MM-DD), area_m2 (float), total_price (float),
        price_per_m2 (float)

    Args:
        transactions: list of MoJ transaction dicts
        target_area_m2: subject property plot area
        target_date: valuation date (default: now)
        trend_slope_annual: annual % price change for this area (e.g. -3.4)
        location_adj_pct: sub-location adjustment from GIS factors (e.g. +2.5)

    Returns:
        AdjustedResult with per-transaction adjustments and adjusted median
    """
    if not transactions:
        return None

    if target_date is None:
        target_date = datetime.now()

    target_bracket, target_mult = _bracket_for(target_area_m2)
    monthly_trend = trend_slope_annual / 12.0 / 100.0  # convert annual % to monthly fraction

    adjusted = []
    for txn in transactions:
        price_m2 = txn.get('price_per_m2') or txn.get('price_m2')
        total = txn.get('total_price') or txn.get('total')
        area = txn.get('area_m2')

        if not price_m2 or not area or price_m2 <= 0:
            continue

        if not total:
            total = price_m2 * area

        notes = []

        # 1. TIME ADJUSTMENT
        time_adj = 0.0
        txn_date_str = txn.get('date', '')
        try:
            txn_date = datetime.strptime(str(txn_date_str), '%Y-%m-%d')
            months_diff = (target_date - txn_date).days / 30.44
            time_adj = months_diff * monthly_trend
            if abs(time_adj) > 0.001:
                direction = 'تعديل زمني' + (' ↑' if time_adj > 0 else ' ↓')
                notes.append(f'{direction} {abs(time_adj)*100:.1f}% ({months_diff:.0f} شهر)')
        except (ValueError, TypeError):
            notes.append('لا يوجد تاريخ — بدون تعديل زمني')

        # 2. SIZE ADJUSTMENT
        txn_bracket, txn_mult = _bracket_for(area)
        size_adj = 0.0
        if txn_bracket != target_bracket and txn_mult > 0:
            # Adjust from txn bracket to target bracket
            size_adj = (target_mult / txn_mult) - 1.0
            notes.append(f'تعديل حجم {size_adj*100:+.1f}% '
                        f'(من {txn_bracket[0]}-{txn_bracket[1]}م² إلى {target_bracket[0]}-{target_bracket[1]}م²)')

        # 3. LOCATION (passed in — from GIS factors)
        loc_adj = location_adj_pct / 100.0 if location_adj_pct else 0.0

        # 4. CONDITION — MoJ has no condition data
        # We acknowledge this as an explicit unknown
        notes.append('حالة المبنى: غير معروفة من MoJ — تحفظ مادي')

        # Apply adjustments
        total_mult = 1.0 + time_adj + size_adj + loc_adj
        adj_price_m2 = price_m2 * total_mult
        adj_total = adj_price_m2 * target_area_m2

        adjusted.append(TransactionAdjustment(
            date=txn_date_str,
            area_m2=area,
            total_price=round(total),
            price_per_m2=round(price_m2),
            time_adj_pct=round(time_adj * 100, 2),
            size_adj_pct=round(size_adj * 100, 2),
            location_adj_pct=round(loc_adj * 100, 2),
            adjusted_price_per_m2=round(adj_price_m2),
            adjusted_total=round(adj_total),
            adjustment_notes=notes,
        ))

    if not adjusted:
        return None

    # Compute adjusted median
    adj_prices = sorted(a.adjusted_price_per_m2 for a in adjusted)
    raw_prices = sorted(a.price_per_m2 for a in adjusted)
    n = len(adj_prices)
    p = lambda vals, q: vals[int(q * (n - 1))]

    raw_med = p(raw_prices, 0.5)
    adj_med = p(adj_prices, 0.5)
    adj_p25 = p(adj_prices, 0.25)
    adj_p75 = p(adj_prices, 0.75)

    caveats = [
        'حالة المبنى غير معروفة من بيانات وزارة العدل — تحفظ مادي (RICS Material Uncertainty).',
        'الموقع الدقيق داخل المنطقة غير مميَّز في البيانات.',
    ]
    if n < 20:
        caveats.insert(0, f'حجم العينة محدود (n={n}). التعديلات إرشادية.')

    return AdjustedResult(
        raw_median_per_m2=round(raw_med),
        adjusted_median_per_m2=round(adj_med),
        adjusted_median_total=round(adj_med * target_area_m2),
        adjusted_low=round(adj_p25 * target_area_m2),
        adjusted_high=round(adj_p75 * target_area_m2),
        n=n,
        target_area_m2=target_area_m2,
        trend_used_pct=trend_slope_annual,
        adjustment_table=adjusted,
        method_note=(
            f'تم تعديل {n} صفقة مقارنة فردياً: '
            f'زمنياً ({trend_slope_annual:+.1f}%/سنة)، '
            f'حجمياً (شريحة {target_bracket[0]}-{target_bracket[1]}م²). '
            f'الوسيط الخام {raw_med:,} → الوسيط المُعدَّل {adj_med:,} ر.ق/م².'
        ),
        caveats=caveats,
    )

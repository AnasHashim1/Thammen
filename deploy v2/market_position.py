#!/usr/bin/env python3
"""
market_position.py — وصف موضع السعر بدون توصية شرائية.

هذا الملف يحلّ محل verdict في النظام السابق. الفرق الجوهري:
    قبل: 'BARGAIN' / 'REJECT' / 'OVERPRICED' (أحكام شرائية = مسؤولية قانونية)
    بعد: 'below_market' / 'at_market' / 'above_market' (وصف موضعي فقط)

ثمّن لا يقول للعميل "اشترِ" أو "لا تشترِ". ثمّن يقول:
    "هذا السعر مقابل ما عرفه السوق، أنت تقرّر."

Usage:
    from market_position import compute_position
    pos = compute_position(
        listing_price=2400000,
        benchmark_price=2174000,
        benchmark_source='MoJ median (n=71, الوكير، آخر 24 شهر)',
    )
    print(pos.position_label)        # 'above_market'
    print(pos.gap_pct)               # 10.4
    print(pos.description_ar)        # نص عربي
"""

from dataclasses import dataclass, field
from typing import Optional, List


# الحدود الموضعية — وصفية، ليست توصيات
# ±10% طبيعي للسوق، ±25% انحراف ملحوظ
NORMAL_BAND_PCT = 10
SIGNIFICANT_BAND_PCT = 25


@dataclass
class MarketPosition:
    """
    موضع السعر مقابل المرجع — وصف فقط، بلا توصية.

    الحقل position_label من القيم التالية:
        'far_below_market'   → أكثر من -25% تحت المرجع
        'below_market'       → بين -10% و -25%
        'at_market'          → بين -10% و +10% (طبيعي)
        'above_market'       → بين +10% و +25%
        'far_above_market'   → أكثر من +25% فوق المرجع
        'no_benchmark'       → لا يوجد مرجع كافٍ للمقارنة

    لاحظ: لا يوجد 'BARGAIN' / 'OVERPRICED' / 'REJECT' / 'BUY' / 'SELL'.
    العميل هو من يفسّر الموضع ويتخذ القرار.
    """
    listing_qar: Optional[float] = None
    benchmark_qar: Optional[float] = None
    benchmark_source: str = ''
    benchmark_n: Optional[int] = None        # حجم العينة وراء المرجع
    gap_qar: Optional[float] = None
    gap_pct: Optional[float] = None
    position_label: str = 'no_benchmark'
    description_ar: str = ''

    # تحفظات إن وُجدت
    caveats: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            'listing_qar': self.listing_qar,
            'benchmark_qar': self.benchmark_qar,
            'benchmark_source': self.benchmark_source,
            'benchmark_n': self.benchmark_n,
            'gap_qar': self.gap_qar,
            'gap_pct': self.gap_pct,
            'position_label': self.position_label,
            'description_ar': self.description_ar,
            'caveats': self.caveats,
        }


def _classify_position(gap_pct: float) -> str:
    """تصنيف الموضع بناءً على الفجوة. وصفي فقط."""
    if gap_pct < -SIGNIFICANT_BAND_PCT:
        return 'far_below_market'
    elif gap_pct < -NORMAL_BAND_PCT:
        return 'below_market'
    elif gap_pct <= NORMAL_BAND_PCT:
        return 'at_market'
    elif gap_pct <= SIGNIFICANT_BAND_PCT:
        return 'above_market'
    else:
        return 'far_above_market'


def _describe_position_ar(label: str, gap_pct: float, n: Optional[int]) -> str:
    """وصف عربي للموضع — وصفي فقط، يُحفّز التحقق لا الإجراء."""
    n_str = f" (مرجع n={n})" if n else ""

    if label == 'no_benchmark':
        return "لا يوجد مرجع كافٍ للمقارنة. تحقق من إعلانات مماثلة في المنطقة."

    if label == 'at_market':
        return (f"السعر ضمن النطاق الطبيعي للسوق (انحراف {gap_pct:+.1f}%){n_str}. "
                f"المراجعة الميدانية والتفاوض هي العوامل الفارقة.")

    if label == 'below_market':
        return (f"السعر أقل من المرجع بـ {abs(gap_pct):.1f}%{n_str}. "
                f"تحقّق من سبب الفرق: حالة العقار، التزامات (تنازل/أقساط)، "
                f"حالة الملكية، عمر البناء.")

    if label == 'far_below_market':
        return (f"السعر أقل من المرجع بـ {abs(gap_pct):.1f}%{n_str} — فرق كبير غير معتاد. "
                f"الفروقات بهذا الحجم عادةً لها سبب: مشاكل قانونية (تنازل، خلاف، بدون فرز)، "
                f"حالة سيئة (يحتاج هدم/ترميم)، التزامات مالية (أقساط)، أو معلومة الإعلان مغلوطة. "
                f"التحقق إجباري قبل أي تقدّم.")

    if label == 'above_market':
        return (f"السعر أعلى من المرجع بـ {gap_pct:.1f}%{n_str}. "
                f"قد يكون مبرّراً (تشطيبات أعلى، موقع مميز، إطلالة) أو غير مبرّر. "
                f"قارن بإعلانات مماثلة في نفس البرج/المجمع.")

    if label == 'far_above_market':
        return (f"السعر أعلى من المرجع بـ {gap_pct:.1f}%{n_str} — فرق كبير. "
                f"إن لم تكن المبرّرات (موقع/مساحة/تشطيب) واضحة، السوق غالباً لن يقبل هذا السعر "
                f"وسيمكث الإعلان طويلاً.")

    return ""


def compute_position(
    listing_price: Optional[float] = None,
    benchmark_price: Optional[float] = None,
    benchmark_source: str = '',
    benchmark_n: Optional[int] = None,
    listing_caveats: Optional[List[str]] = None,
) -> MarketPosition:
    """
    احسب الموضع السعري وصفياً.

    Args:
        listing_price: سعر الإعلان (ر.ق)
        benchmark_price: المرجع المُقارَن به (مثلاً MoJ median × عوامل GIS)
        benchmark_source: وصف مصدر المرجع للشفافية
        benchmark_n: حجم العينة وراء المرجع (للسياق)
        listing_caveats: تحفظات على الإعلان (red flags، غموض، إلخ)

    Returns:
        MarketPosition — كائن وصفي بلا توصية
    """
    if not (listing_price and benchmark_price and benchmark_price > 0):
        return MarketPosition(
            listing_qar=listing_price,
            benchmark_qar=benchmark_price,
            benchmark_source=benchmark_source,
            position_label='no_benchmark',
            description_ar='لا يوجد سعر مُعلن أو مرجع كافٍ.',
            caveats=listing_caveats or [],
        )

    gap_qar = listing_price - benchmark_price
    gap_pct = (gap_qar / benchmark_price) * 100
    label = _classify_position(gap_pct)
    desc = _describe_position_ar(label, gap_pct, benchmark_n)

    return MarketPosition(
        listing_qar=listing_price,
        benchmark_qar=benchmark_price,
        benchmark_source=benchmark_source,
        benchmark_n=benchmark_n,
        gap_qar=gap_qar,
        gap_pct=round(gap_pct, 1),
        position_label=label,
        description_ar=desc,
        caveats=listing_caveats or [],
    )


# ============================================================
# CLI للاختبار
# ============================================================
if __name__ == '__main__':
    print("═" * 70)
    print("اختبار market_position")
    print("═" * 70)

    test_cases = [
        # (listing, benchmark, source, n, caveats)
        (2_400_000, 2_174_000, 'MoJ الوكير 400-600م² فلل', 71, []),
        (2_050_000, 2_174_000, 'MoJ الوكير 400-600م² فلل', 71, []),
        (1_500_000, 2_174_000, 'MoJ الوكير 400-600م² فلل', 71, []),
        (1_200_000, 2_174_000, 'MoJ الوكير 400-600م² فلل', 71, ['تنازل', 'أقساط متبقية']),
        (3_500_000, 2_174_000, 'MoJ الوكير 400-600م² فلل', 71, []),
        (2_174_000, 2_174_000, 'MoJ الوكير 400-600م² فلل', 71, []),
        (2_400_000, None, '', None, []),  # no benchmark
    ]

    for listing, bench, source, n, caveats in test_cases:
        pos = compute_position(listing, bench, source, n, caveats)
        listing_str = f"{listing:,.0f}" if listing else "N/A"
        bench_str = f"{bench:,.0f}" if bench else "N/A"
        gap_str = f"{pos.gap_pct:+.1f}%" if pos.gap_pct is not None else "—"

        print(f"\nإعلان: {listing_str:>12} | مرجع: {bench_str:>12} | فجوة: {gap_str:>7}")
        print(f"  → {pos.position_label}")
        print(f"  وصف: {pos.description_ar}")
        if pos.caveats:
            print(f"  تحفظات: {pos.caveats}")

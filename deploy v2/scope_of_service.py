#!/usr/bin/env python3
"""
scope_of_service.py — Sprint 2.14.0

Formal RICS VPS 1 (Terms of engagement / scope of work) Scope of Service declaration for Thammen.

WHY THIS EXISTS:
  RICS Red Book Global Standards (effective 31 January 2025) VPS 1
  (Terms of engagement / scope of work) requires every valuation to be
  accompanied by a clear statement of scope:
    - What is being valued (asset type, address, interest)
    - What is NOT included (assets out of scope, limitations)
    - Level of investigation (inspection / desktop / drive-by)
    - Methodology applied (Sales Comparison / Cost / Income)
    - Service level (Valuation Report / Calculation of Value / Other Advice)

  Thammen's accuracy depends entirely on the asset type and area having
  sufficient MoJ comparable transactions. For some asset classes (e.g.
  apartments, palaces, commercial), this condition can never be met
  from publicly available data — yet the engine has historically been
  silent about this limitation, leaving users with no signal.

  Sprint 2.14.0 makes scope explicit at three levels:
    1. Globally on the homepage (what Thammen supports vs not)
    2. Per address as part of the API response (asset-level scope check)
    3. In the UI before any number is shown (so users self-filter)

DESIGN PRINCIPLES:
  1. Honest categorisation. No category is described as supported unless
     we can actually produce a defensible Sales Comparison or Income
     approach valuation with available data.
  2. Three-tier classification, not binary supported/unsupported:
     - SUPPORTED: full Sales Comparison from MoJ + standard adjustments
     - LIMITED: requires user-provided inputs (income, listing price) +
       carries elevated uncertainty by definition
     - UNSUPPORTED: explicitly declined; no number produced
  3. Honest service level. Thammen is a "Calculation of Value" plus
     "Other Advice" (RICS PS 1 / VPS 1.4) — NOT a Valuation Report.
     We say so plainly.

USAGE:
  from scope_of_service import (
      classify_asset_scope,
      service_scope_summary,
      AssetScope,
  )

  scope = classify_asset_scope('standalone_villa')
  scope.tier              # 'supported'
  scope.methodology_ar    # 'مقارنة المبيعات (Sales Comparison)'
  scope.disclaimer_ar     # the user-facing disclaimer
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional


# ─── Service-level declaration (RICS PS 1 / VPS 1) ────────────────────────
#
# Thammen does NOT produce "Valuation Reports" per RICS Red Book. It produces:
#   1. "Calculation of Value" — the `valuation.amount` field (Sales Comparison)
#   2. "Other Advice" — the negotiation guidance, market position, briefs
#
# This distinction is critical: it determines what regulatory framework
# applies. Valuation Reports must follow all VPS standards strictly. Other
# Advice follows only the standards that apply to consultancy.
#
# Per RICS PS 1.5.1: "Valuations that fall within the categories listed in
# VPS 1 paragraph 1.2 are subject to mandatory compliance." Thammen's
# valuations are NOT for mortgage, financial reporting, or judicial purposes
# — so mandatory VPS 1 compliance does not technically apply. We voluntarily
# follow VPS 3 methodology as best practice, but we are clear about scope.

SERVICE_LEVEL_AR = (
    'ثمّن يُنتج "حساب قيمة" (Calculation of Value) + "نصيحة استشارية" '
    '(Other Advice) وفق المنهجية المعيارية لـ ‎RICS VPS 3‎ — وليس "تقريراً '
    'تقييمياً معتمداً" (Valuation Report). للأغراض الرسمية (قروض، نزاعات '
    'قضائية، تقارير محاسبية، تأمين)، يلزم تقييم معتمد من مُقيِّم مُرخّص.'
)

SERVICE_LEVEL_EN = (
    'Thammen provides a "Calculation of Value" + "Other Advice" following '
    'RICS VPS 3 methodology as best practice — NOT a certified "Valuation '
    'Report". For regulatory purposes (mortgages, court proceedings, '
    'financial reporting, insurance), a certified valuation by a licensed '
    'RICS valuer is required.'
)


# ─── Asset-type scope classification ──────────────────────────────────────

@dataclass(frozen=True)
class AssetScope:
    """Scope assessment for a single asset type."""
    asset_type: str
    tier: str                      # 'supported' | 'limited' | 'unsupported'
    label_ar: str
    methodology_ar: str            # primary approach (Sales Comparison / Cost / Income)
    methodology_en: str
    requires_user_input_ar: Optional[str]   # what extra inputs are required (if limited)
    disclaimer_ar: str             # user-facing scope disclaimer
    reason_ar: str                 # explanation of tier classification


# Authoritative mapping. Update only with field evidence.
#
# Tier criteria:
#   supported    — sufficient MoJ comparables in MoJ for >5 areas,
#                  Sales Comparison methodology applicable directly
#   limited      — DCF / Income-only methodology, requires user inputs
#                  (rental income or listing price) — engine cannot stand alone
#   unsupported  — neither MoJ comparables nor a defensible alternative
#                  exist; engine should refuse rather than guess

_ASSET_SCOPE = {
    # ── Supported (Sales Comparison from MoJ) ───────────────────────────
    'standalone_villa': AssetScope(
        asset_type='standalone_villa',
        tier='supported',
        label_ar='فلة مستقلة',
        methodology_ar='مقارنة المبيعات (Sales Comparison) من سجلات وزارة العدل',
        methodology_en='Sales Comparison from MoJ registered transactions',
        requires_user_input_ar=None,
        disclaimer_ar=(
            'تقييم الفلل المستقلة يستخدم مقارنة مع صفقات وزارة العدل في '
            'نفس المنطقة والشريحة (نافذة 24 شهراً). لا يدخل في التقييم '
            'تأثير حالة المبنى الداخلية، التشطيبات، أو الإطلالة.'
        ),
        reason_ar='تغطية MoJ كافية في 10+ مناطق سكنية رئيسية',
    ),
    'land': AssetScope(
        asset_type='land',
        tier='supported',
        label_ar='أرض سكنية',
        methodology_ar='مقارنة المبيعات (Sales Comparison) من سجلات وزارة العدل',
        methodology_en='Sales Comparison from MoJ registered transactions',
        requires_user_input_ar=None,
        disclaimer_ar=(
            'تقييم الأراضي السكنية يستخدم مقارنة مع صفقات الأراضي الفضاء '
            'في نفس المنطقة والشريحة. خصائص خاصة كالقرب من شارع رئيسي، '
            'الزاوية، أو الإطلالة قد ترفع السعر الفعلي 10-30% فوق هذا التقدير.'
        ),
        reason_ar='تغطية MoJ كافية وأسعار الأرض مستقرة نسبياً',
    ),
    'compound_small': AssetScope(
        asset_type='compound_small',
        tier='supported',
        label_ar='مجمع صغير (≤15K م²)',
        methodology_ar='مقارنة المبيعات (Sales Comparison) — تصنيف "مجمع فلل" في وزارة العدل',
        methodology_en='Sales Comparison — "Villa Compound" classification in MoJ',
        requires_user_input_ar=None,
        disclaimer_ar=(
            'تقييم المجمعات الصغيرة يستخدم سجلات "مجمع فلل" في وزارة العدل. '
            'يصلح للمجمعات حتى 15,027 م² (أكبر مجمع فلل مسجّل في وزارة العدل). '
            'المجمعات الأكبر تحتاج منهجية الدخل (Income Approach).'
        ),
        reason_ar='سجلات "مجمع فلل" متوفرة لمجمعات حتى 15K م²',
    ),

    # ── Limited (Income/DCF, requires user inputs) ──────────────────────
    'compound_large': AssetScope(
        asset_type='compound_large',
        tier='limited',
        label_ar='مجمع كبير (≥50K م²)',
        methodology_ar='منهج الدخل (Income Approach) — معدّل الرسملة على إيجار سنوي',
        methodology_en='Income Approach — capitalisation rate applied to annual rent',
        requires_user_input_ar='الإيجار السنوي الإجمالي للمجمع (Gross Annual Income)',
        disclaimer_ar=(
            'المجمعات الكبيرة لا توجد لها مقارنات مباشرة في وزارة العدل. '
            'التقييم يعتمد على منهج الدخل ويتطلب إفادة الإيجار السنوي الإجمالي. '
            'بدون هذه الإفادة، يقدّم ثمّن تصنيفاً فقط دون رقم.'
        ),
        reason_ar='لا توجد مقارنات MoJ لأصول ≥50K م²، المنهج المعياري هو الدخل',
    ),
    'tower': AssetScope(
        asset_type='tower',
        tier='limited',
        label_ar='برج كامل',
        methodology_ar='منهج الدخل (Income Approach)',
        methodology_en='Income Approach',
        requires_user_input_ar='الإيجار السنوي الإجمالي للبرج',
        disclaimer_ar=(
            'الأبراج تُسجَّل بأرقام مرجعية موحَّدة في وزارة العدل بدلاً من '
            'مقارنات سعر/م². التقييم يتطلب إفادة الدخل التشغيلي السنوي.'
        ),
        reason_ar='لا توجد مقارنات MoJ سعر/م² للأبراج',
    ),
    'apartment_building': AssetScope(
        asset_type='apartment_building',
        tier='limited',
        label_ar='عمارة شقق',
        methodology_ar='منهج الدخل (Income Approach)',
        methodology_en='Income Approach',
        requires_user_input_ar='الإيجار السنوي الإجمالي',
        disclaimer_ar=(
            'عمارات الشقق تُقيَّم بمنهج الدخل. وزارة العدل لا تسجل وحدات '
            'الشقق فردياً بشكل قابل للمقارنة. الإيجار السنوي مطلوب.'
        ),
        reason_ar='MoJ لا تسجل وحدات الشقق فردياً',
    ),
    'palace': AssetScope(
        asset_type='palace',
        tier='limited',
        label_ar='قصر',
        methodology_ar='تركيب قيمة الأرض + تكلفة البناء (Cost Approach) — تقريبي',
        methodology_en='Land Value + Cost Approach — approximate',
        requires_user_input_ar='ميزانية البناء الأصلية (إن أمكن) ومساحة البناء الإجمالية',
        disclaimer_ar=(
            'القصور (>3,000 م² قطعة) ليس لها مقارنات MoJ كافية (n=5 شركاء '
            'فقط في كامل قطر). التقدير يتركّب من قيمة الأرض + تكلفة بناء '
            'تقديرية. الفروقات الفعلية مع السوق قد تصل ±30%.'
        ),
        reason_ar='عينة MoJ قصور ضعيفة جداً (n=5 شركاء فقط)',
    ),

    # ── Unsupported (engine should refuse) ──────────────────────────────
    'commercial': AssetScope(
        asset_type='commercial',
        tier='unsupported',
        label_ar='عقار تجاري',
        methodology_ar='غير مطبَّق',
        methodology_en='Not applicable',
        requires_user_input_ar=None,
        disclaimer_ar=(
            'العقارات التجارية (محلات، مكاتب، مولات) خارج نطاق ثمّن. '
            'بيانات الإيجارات والصفقات التجارية غير متاحة عبر مصادر عامة. '
            'يلزم التواصل مع شركات تقييم متخصصة (Cushman & Wakefield، JLL، '
            'Knight Frank Qatar).'
        ),
        reason_ar='لا توجد بيانات تجارية عامة في قطر',
    ),
    'industrial': AssetScope(
        asset_type='industrial',
        tier='unsupported',
        label_ar='عقار صناعي',
        methodology_ar='غير مطبَّق',
        methodology_en='Not applicable',
        requires_user_input_ar=None,
        disclaimer_ar=(
            'العقارات الصناعية والمستودعات خارج نطاق ثمّن. '
            'تقييمها يتطلب خبرة متخصصة في التصنيف الصناعي والاستخدام.'
        ),
        reason_ar='خارج نطاق الإصدار الحالي',
    ),
    'agricultural': AssetScope(
        asset_type='agricultural',
        tier='unsupported',
        label_ar='مزرعة / أرض زراعية',
        methodology_ar='غير مطبَّق',
        methodology_en='Not applicable',
        requires_user_input_ar=None,
        disclaimer_ar=(
            'المزارع والأراضي الزراعية خارج نطاق ثمّن. تقييمها يعتمد على '
            'جودة التربة، حقوق المياه، الإنتاجية — عوامل غير متاحة بالنسبة لنا.'
        ),
        reason_ar='خارج نطاق الإصدار الحالي',
    ),
}

# Sprint 2.21.0.5: alias — the classifier emits 'raw_land' (AssetType.RAW_LAND),
# while this table is keyed 'land'. Treat raw_land as the supported land scope so
# a bare-land PIN evaluation isn't mislabelled "نوع غير معروف / خارج النطاق".
# (Alias pattern, not rename — see Operational_Rules #47.)
_ASSET_SCOPE['raw_land'] = _ASSET_SCOPE['land']


# ─── Public API ───────────────────────────────────────────────────────────

def classify_asset_scope(asset_type: str) -> AssetScope:
    """Return the scope assessment for an asset type.

    Falls back to a generic 'unknown' assessment for unrecognised types.
    """
    if asset_type in _ASSET_SCOPE:
        return _ASSET_SCOPE[asset_type]
    # Unknown type — default to unsupported with explicit reason
    return AssetScope(
        asset_type=asset_type or 'unknown',
        tier='unsupported',
        label_ar='نوع غير معروف',
        methodology_ar='غير مطبَّق',
        methodology_en='Not applicable',
        requires_user_input_ar=None,
        disclaimer_ar=(
            'لم نتمكن من تصنيف هذا العقار. التصنيف الصحيح للأصل ضروري '
            'لتطبيق المنهجية المناسبة. يرجى مراجعة العنوان المُدخَل.'
        ),
        reason_ar='تصنيف غير مطابق لأي فئة مدعومة',
    )


def scope_to_dict(scope: AssetScope) -> dict:
    """Serialize an AssetScope for API responses."""
    return {
        'asset_type': scope.asset_type,
        'tier': scope.tier,
        'label_ar': scope.label_ar,
        'methodology_ar': scope.methodology_ar,
        'methodology_en': scope.methodology_en,
        'requires_user_input_ar': scope.requires_user_input_ar,
        'disclaimer_ar': scope.disclaimer_ar,
        'reason_ar': scope.reason_ar,
    }


def service_scope_summary() -> dict:
    """Return a homepage-ready summary of what Thammen does and doesn't.

    Used by /api/about and the homepage scope card.
    """
    supported = []
    limited = []
    unsupported = []
    for s in _ASSET_SCOPE.values():
        entry = {
            'asset_type': s.asset_type,
            'label_ar': s.label_ar,
            'reason_ar': s.reason_ar,
        }
        if s.tier == 'supported':
            supported.append(entry)
        elif s.tier == 'limited':
            entry['requires'] = s.requires_user_input_ar
            limited.append(entry)
        else:
            unsupported.append(entry)

    return {
        'service_level_ar': SERVICE_LEVEL_AR,
        'service_level_en': SERVICE_LEVEL_EN,
        'supported': supported,
        'limited': limited,
        'unsupported': unsupported,
        'summary_ar': (
            f'ثمّن يدعم {len(supported)} فئات بالكامل، {len(limited)} فئات '
            f'بمنهج الدخل (تتطلب إفادة الإيجار)، و {len(unsupported)} '
            f'فئات خارج النطاق.'
        ),
    }


# ─── CLI self-test ────────────────────────────────────────────────────────

if __name__ == '__main__':
    print('=== Service Scope Summary ===')
    summary = service_scope_summary()
    print(f"\n{summary['summary_ar']}")
    print(f"\nSupported ({len(summary['supported'])}):")
    for s in summary['supported']:
        print(f"  ✅ {s['label_ar']} — {s['reason_ar']}")
    print(f"\nLimited ({len(summary['limited'])}):")
    for s in summary['limited']:
        print(f"  ⚠️  {s['label_ar']} — يتطلب: {s.get('requires', '?')}")
    print(f"\nUnsupported ({len(summary['unsupported'])}):")
    for s in summary['unsupported']:
        print(f"  ❌ {s['label_ar']} — {s['reason_ar']}")
    print(f"\n=== Service Level Declaration ===")
    print(summary['service_level_ar'])

#!/usr/bin/env python3
"""
service_charge_db.py — قاعدة بيانات رسوم الخدمات للعقارات في قطر.

البيانات per-precinct (وليس per-area)، مأخوذة من إعلانات FGRealty الفردية
المُتحقَّق منها (نمط "Service Charge QAR XX/sqm"). مقالات FGRealty المُلخّصة
ليست مرجعاً موثوقاً — اعتمد الإعلانات.

Lookup hierarchy:
    1. مبنى محدد (e.g. "Tower 7 Porto Arabia") إن وُجد
    2. precinct (e.g. "Porto Arabia")
    3. area (e.g. "اللؤلؤة") — متوسط
    4. fallback range — للمناطق غير المعروفة

Usage:
    from service_charge_db import lookup, ServiceChargeRecord
    rec = lookup(area='اللؤلؤة', precinct='Porto Arabia', asset_type='apartment')
    print(rec.monthly_per_m2)         # 15.0
    print(rec.annual_per_m2)          # 180.0
    print(rec.confidence)             # 'verified'
    print(rec.source)                 # 'FGRealty AS-001032 (2026-05)'
"""

from dataclasses import dataclass, field
from typing import Optional, Tuple, List


@dataclass
class ServiceChargeRecord:
    """سجل رسوم خدمات لمنطقة/مجمّع/مبنى محدد."""
    area: Optional[str] = None              # 'اللؤلؤة' / 'لوسيل' / None for any
    precinct: Optional[str] = None          # 'Porto Arabia' / 'Fox Hills' / None
    building: Optional[str] = None          # 'Tower 7' / None
    asset_type: str = 'apartment'           # 'apartment' / 'villa_standalone' / 'villa_compound'

    # الرقم الرئيسي
    monthly_per_m2: Optional[float] = None  # ر.ق/م²/شهر (الصيغة المُعلَنة في FGRealty)

    # نطاق احتياطي عند غياب الرقم المحدد
    monthly_per_m2_range: Optional[Tuple[float, float]] = None

    # المتاداتا — حاسمة للشفافية
    source: str = ''                        # مرجع الإعلان أو ملاحظة
    source_date: str = ''                   # YYYY-MM
    confidence: str = 'reported'            # 'verified' | 'reported' | 'estimated'
    notes: str = ''

    @property
    def annual_per_m2(self) -> Optional[float]:
        """الرسوم السنوية لكل متر مربع."""
        return self.monthly_per_m2 * 12 if self.monthly_per_m2 is not None else None

    @property
    def annual_per_m2_range(self) -> Optional[Tuple[float, float]]:
        if self.monthly_per_m2_range:
            lo, hi = self.monthly_per_m2_range
            return (lo * 12, hi * 12)
        return None

    def annual_total(self, bua_m2: float) -> Optional[float]:
        """الرسوم السنوية الكاملة لشقة بمساحة معطاة."""
        if self.annual_per_m2 is not None:
            return self.annual_per_m2 * bua_m2
        if self.annual_per_m2_range:
            lo, hi = self.annual_per_m2_range
            return ((lo + hi) / 2) * bua_m2
        return None

    def to_dict(self) -> dict:
        d = {
            'area': self.area,
            'precinct': self.precinct,
            'building': self.building,
            'asset_type': self.asset_type,
            'monthly_per_m2': self.monthly_per_m2,
            'annual_per_m2': self.annual_per_m2,
            'source': self.source,
            'source_date': self.source_date,
            'confidence': self.confidence,
            'notes': self.notes,
        }
        if self.monthly_per_m2_range:
            d['monthly_per_m2_range'] = list(self.monthly_per_m2_range)
            d['annual_per_m2_range'] = list(self.annual_per_m2_range)
        return d


# ============================================================
# قاعدة البيانات — مُتحقَّقة من إعلانات FGRealty الفردية
# المرجع: نمط "Service Charge QAR XX/sqm" في حقل Property charges
# ============================================================

SERVICE_CHARGE_DB: List[ServiceChargeRecord] = [

    # ═════════════════════════════════════════════════
    # اللؤلؤة (The Pearl) — verified from FGRealty listings
    # ═════════════════════════════════════════════════

    # Porto Arabia — مُتحقَّق من إعلانين منفصلين
    ServiceChargeRecord(
        area='اللؤلؤة', precinct='Porto Arabia', asset_type='apartment',
        monthly_per_m2=15.0,  # = 180 ر.ق/م²/سنة
        source='FGRealty AS-001032 (3BR 307m²) + AS-003429 (2BR 160m², 2400/شهر إجمالي)',
        source_date='2026-05',
        confidence='verified',
        notes='عينتان مستقلتان أعطتا نفس النتيجة؛ يختلف بين أبراج Porto Arabia ضمن نطاق ±10%'
    ),

    # Qanat Quartier — مُتحقَّق
    ServiceChargeRecord(
        area='اللؤلؤة', precinct='Qanat Quartier', asset_type='apartment',
        monthly_per_m2=14.0,  # = 168 ر.ق/م²/سنة
        source='FGRealty AS-000750 (1BR 88m²)',
        source_date='2026-05',
        confidence='verified',
        notes='Qanat Quartier أقل قليلاً من Porto Arabia لأنه low-rise (لا مصاعد كبيرة)'
    ),

    # St. Regis Townhouse — مُتحقَّق (حالة خاصة)
    ServiceChargeRecord(
        area='اللؤلؤة', precinct='St. Regis Marsa Arabia', asset_type='townhouse',
        monthly_per_m2=0.0,
        source='FGRealty TS-000124 (4BR 500m² private pool)',
        source_date='2026-05',
        confidence='verified',
        notes='townhouse مع حمام سباحة خاص — لا توجد مرافق مشتركة، الرسوم 0'
    ),

    # اللؤلؤة fallback — أي precinct غير مذكور
    ServiceChargeRecord(
        area='اللؤلؤة', precinct=None, asset_type='apartment',
        monthly_per_m2=16.0,  # متوسط ~192 ر.ق/م²/سنة
        monthly_per_m2_range=(14.0, 18.0),  # 168-216 سنوياً
        source='market_average across observed Pearl precincts',
        source_date='2026-05',
        confidence='reported',
        notes='النطاق ±20% بحسب البرج؛ الأبراج الفاخرة (Marina Gate, Ferrari Tower) في الحد الأعلى'
    ),

    # ═════════════════════════════════════════════════
    # لوسيل (Lusail) — verified from FGRealty listings
    # ═════════════════════════════════════════════════

    # Fox Hills — مُتحقَّق (مساكن متوسطة)
    ServiceChargeRecord(
        area='لوسيل', precinct='Fox Hills', asset_type='apartment',
        monthly_per_m2=10.0,  # = 120 ر.ق/م²/سنة
        source='FGRealty AS-002329 (2BR 94m² Damac Piazza)',
        source_date='2026-05',
        confidence='verified',
        notes='Fox Hills mid-rise — أقل المرافق من اللؤلؤة'
    ),

    # Marina District / Place Vendome area — مُتحقَّق
    ServiceChargeRecord(
        area='لوسيل', precinct='Marina', asset_type='apartment',
        monthly_per_m2=14.0,  # = 168 ر.ق/م²/سنة
        source='FGRealty AS-002710 (1BR 113m² Place Vendome view)',
        source_date='2026-05',
        confidence='verified',
        notes='قريب من اللؤلؤة في الرسوم — مرافق مماثلة'
    ),

    # Al Kharayej — مُتحقَّق
    ServiceChargeRecord(
        area='لوسيل', precinct='Al Kharayej', asset_type='apartment',
        monthly_per_m2=14.5,  # ≈ 174 ر.ق/م²/سنة (1664/شهر / 115م²)
        source='FGRealty AS-003398 (2BR 115m², 1664/شهر إجمالي)',
        source_date='2026-05',
        confidence='verified',
    ),

    # لوسيل fallback
    ServiceChargeRecord(
        area='لوسيل', precinct=None, asset_type='apartment',
        monthly_per_m2=11.0,  # متوسط ~132 ر.ق/م²/سنة
        monthly_per_m2_range=(8.0, 14.0),  # 96-168 سنوياً
        source='market_average across observed Lusail precincts',
        source_date='2026-05',
        confidence='reported',
        notes='النطاق ±35% بحسب المنطقة الفرعية'
    ),

    # ═════════════════════════════════════════════════
    # الفلل المستقلة — لا اتحاد ملاك
    # ═════════════════════════════════════════════════
    ServiceChargeRecord(
        area=None, precinct=None, asset_type='villa_standalone',
        monthly_per_m2=0.0,
        source='no_HOA_for_standalone_villas',
        source_date='2026-05',
        confidence='verified',
        notes='الفلل المنفردة في قطر بلا اتحاد ملاك؛ المالك يدفع الصيانة مباشرة'
    ),

    # ═════════════════════════════════════════════════
    # Fallback عام — لمناطق غير مُغطَّاة
    # ═════════════════════════════════════════════════
    ServiceChargeRecord(
        area=None, precinct=None, asset_type='apartment',
        monthly_per_m2=None,
        monthly_per_m2_range=(5.0, 12.0),  # نطاق محافظ 60-144 سنوياً
        source='conservative_market_estimate',
        source_date='2026-05',
        confidence='estimated',
        notes='الشقق العادية خارج اللؤلؤة/لوسيل؛ يجب التحقق من إعلانات المنطقة المحددة'
    ),

    # ═════════════════════════════════════════════════
    # كومباوندات الفلل (مع مرافق مشتركة)
    # ═════════════════════════════════════════════════
    ServiceChargeRecord(
        area=None, precinct=None, asset_type='villa_compound',
        monthly_per_m2=None,
        monthly_per_m2_range=(3.0, 8.0),  # 36-96 سنوياً (أقل بكثير من الشقق)
        source='market_estimate_for_compounds',
        source_date='2026-05',
        confidence='estimated',
        notes='كومباوندات الفلل تحوي مسبح/جيم/أمن مشترك؛ تتراوح الرسوم 8-15K/سنة لفيلا متوسطة'
    ),
]


# ============================================================
# دالة البحث (Lookup)
# ============================================================

def lookup(area: Optional[str] = None,
           precinct: Optional[str] = None,
           building: Optional[str] = None,
           asset_type: str = 'apartment') -> ServiceChargeRecord:
    """
    البحث عن رسوم الخدمات بترتيب هرمي:
      1. مبنى محدد (إن وُجد في القاعدة)
      2. precinct ضمن المنطقة
      3. متوسط المنطقة (أي precinct)
      4. fallback لنوع الأصل

    دائماً يرجع ServiceChargeRecord — لا يرجع None، حتى لو fallback عام.
    هذا يضمن أن الكود الأعلى لا يحتاج معالجة None.
    """

    # الخطوة 1: مبنى محدد
    if building:
        for r in SERVICE_CHARGE_DB:
            if r.building and r.building == building and r.asset_type == asset_type:
                return r

    # الخطوة 2: precinct ضمن area
    if area and precinct:
        for r in SERVICE_CHARGE_DB:
            if (r.area == area and r.precinct == precinct
                    and r.asset_type == asset_type):
                return r

    # الخطوة 3: متوسط المنطقة (precinct=None)
    if area:
        for r in SERVICE_CHARGE_DB:
            if (r.area == area and r.precinct is None
                    and r.asset_type == asset_type):
                return r

    # الخطوة 4: fallback لنوع الأصل (area=None, precinct=None)
    for r in SERVICE_CHARGE_DB:
        if (r.area is None and r.precinct is None
                and r.asset_type == asset_type):
            return r

    # حالة طارئة: لا يوجد أي سجل
    return ServiceChargeRecord(
        asset_type=asset_type,
        monthly_per_m2=None,
        monthly_per_m2_range=(0.0, 20.0),  # نطاق متّسع جداً
        source='no_data',
        confidence='estimated',
        notes='لا توجد بيانات؛ يجب الاستفسار من الوكيل/المالك مباشرة'
    )


# ============================================================
# Helper: human-readable Arabic description
# ============================================================

def describe_ar(record: ServiceChargeRecord) -> str:
    """وصف عربي للسجل، قابل للإدراج في reasoning_trace."""
    if record.monthly_per_m2 is not None:
        annual = record.annual_per_m2
        location = ' '.join(filter(None, [record.area, record.precinct, record.building]))
        return (f"رسوم خدمات {location or 'عام'}: {record.monthly_per_m2:.1f} "
                f"ر.ق/م²/شهر = {annual:.0f} ر.ق/م²/سنة "
                f"({record.confidence}، مصدر: {record.source})")
    elif record.monthly_per_m2_range:
        lo, hi = record.monthly_per_m2_range
        return (f"رسوم خدمات تقديرية: {lo:.0f}-{hi:.0f} ر.ق/م²/شهر "
                f"({record.confidence}، {record.notes or record.source})")
    else:
        return "بيانات رسوم الخدمات غير متوفرة"


# ============================================================
# CLI للاختبار
# ============================================================
if __name__ == '__main__':
    import sys
    import json

    print("═" * 70)
    print("اختبار service_charge_db")
    print("═" * 70)

    test_cases = [
        ('اللؤلؤة', 'Porto Arabia', None, 'apartment'),
        ('اللؤلؤة', 'Qanat Quartier', None, 'apartment'),
        ('اللؤلؤة', None, None, 'apartment'),  # fallback to area avg
        ('لوسيل', 'Fox Hills', None, 'apartment'),
        ('لوسيل', 'Marina', None, 'apartment'),
        ('لوسيل', None, None, 'apartment'),
        ('الخيسة', None, None, 'villa_standalone'),
        ('الدحيل', None, None, 'apartment'),  # outside DB → fallback
    ]

    for area, precinct, building, asset_type in test_cases:
        rec = lookup(area=area, precinct=precinct, building=building, asset_type=asset_type)
        loc_str = f"{area or '?'}/{precinct or '?'}/{asset_type}"
        if rec.monthly_per_m2 is not None:
            print(f"  {loc_str:<40} → {rec.monthly_per_m2:>5.1f}/شهر | "
                  f"{rec.annual_per_m2:>5.0f}/سنة | {rec.confidence}")
        else:
            lo, hi = rec.monthly_per_m2_range
            print(f"  {loc_str:<40} → نطاق {lo:.0f}-{hi:.0f}/شهر | "
                  f"~{(lo+hi)*6:.0f}/سنة | {rec.confidence}")

    # اختبار حساب الرسوم الإجمالية لشقة 145م² في كل مكان
    print("\n" + "═" * 70)
    print("الرسوم السنوية لشقة 145م² في مناطق مختلفة:")
    print("═" * 70)
    for area, precinct, _, asset_type in test_cases[:6]:
        rec = lookup(area=area, precinct=precinct, asset_type=asset_type)
        annual = rec.annual_total(145)
        print(f"  {area}/{precinct or 'متوسط'}: {annual:>9,.0f} ر.ق/سنة")

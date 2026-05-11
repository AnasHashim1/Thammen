#!/usr/bin/env python3
"""
qatar_area_aliases.py — قاعدة بيانات أسماء المناطق في قطر.

تحلّ مشكلة تعدّد أسماء المنطقة الواحدة في بيانات وزارة العدل وفي GIS.

أمثلة:
    - "مريخ" و "امريخ الجنوبي" منطقة جغرافية واحدة
    - "الثمامة"، "الثمامة 46"، "الثمامة 47"، "الثمامة 50" منطقة واحدة
    - "المعمورة"، "المعمورة 43"، "المعمورة 56" منطقة واحدة

الاستخدام:
    from qatar_area_aliases import get_all_aliases, canonical_name

    # احصل على كل أسماء المعمورة
    aliases = get_all_aliases('المعمورة')
    # → ['المعمورة', 'المعمورة 43', 'المعمورة 56']

    # احصل على الاسم الأساسي لمنطقة فرعية
    canonical = canonical_name('الثمامة 46')
    # → 'ثمامة'
"""

from typing import List, Optional, Dict


# ============================================================
# CORE DATABASE
# ============================================================
# Each entry: canonical_key → {variants: [...], municipalities: [...], notes: ...}

ALIASES_DB: Dict[str, Dict] = {
    # ──────────────────────────────────────
    # NUMBERED ZONE VARIANTS (sub-zones of same area)
    # ──────────────────────────────────────

    'ثمامة': {
        'variants': ['الثمامة', 'الثمامة 46', 'الثمامة 47', 'الثمامة 50'],
        'municipalities': ['الدوحة', 'الوكرة'],
        'total_n': 1340,
        'notes': 'الثمامة منطقة كبيرة مقسّمة لزونات. كلها سكنية R1/R2.',
    },

    'معيذر': {
        'variants': ['معيذر', 'معيذر 53', 'معيذر 55'],
        'municipalities': ['الريان'],
        'total_n': 1138,
        'notes': 'معيذر منطقة سكنية واحدة في الريان مقسّمة لزونات.',
    },

    'نعيجة': {
        'variants': ['نعيجة', 'نعيجة 41', 'نعيجة 43', 'نعيجة 44'],
        'municipalities': ['الدوحة'],
        'total_n': 692,
        'notes': 'نعيجة منطقة كبيرة في الدوحة مقسّمة لأربعة زونات.',
    },

    'ازغوى': {
        'variants': ['ازغوى', 'ازغوى 51', 'ازغوى 71'],
        'municipalities': ['الريان', 'أم صلال'],
        'total_n': 534,
        'notes': 'ازغوى منطقة تمتد بين الريان وأم صلال.',
    },

    'معمورة': {
        'variants': ['المعمورة', 'المعمورة 43', 'المعمورة 56'],
        'municipalities': ['الريان', 'الدوحة'],
        'total_n': 277,
        'notes': 'المعمورة منطقة سكنية واحدة مجاورة لبو هامور.',
    },

    'عنيزة': {
        'variants': ['عنيزة', 'عنيزة 63', 'عنيزة 65', 'عنيزة 66'],
        'municipalities': ['الدوحة'],
        'total_n': 185,
        'notes': 'عنيزة في الدوحة، مقسّمة لزونات.',
    },

    'لوسيل': {
        'variants': ['لوسيل', 'لوسيل 69'],
        'municipalities': ['الدوحة', 'الظعاين'],
        'total_n': 175,
        'notes': 'مدينة لوسيل الجديدة. زون 69 = منطقة Fox Hills.',
    },

    'غانم العتيق': {
        'variants': ['الغانم العتيق', 'الغانم العتيق 16', 'الغانم العتيق 6'],
        'municipalities': ['الدوحة'],
        'total_n': 164,
    },

    'سد': {
        'variants': ['السد', 'السد 38', 'السد 39'],
        'municipalities': ['الدوحة'],
        'total_n': 143,
        'notes': 'السد منطقة تجارية/سكنية مختلطة في الدوحة.',
    },

    'فريج بن محمود': {
        'variants': ['فريج بن محمود', 'فريج بن محمود 22', 'فريج بن محمود 23'],
        'municipalities': ['الدوحة'],
        'total_n': 133,
    },

    'فريج السودان': {
        'variants': ['فريج السودان', 'فريج السودان 54', 'فريج السودان 55'],
        'municipalities': ['الريان'],
        'total_n': 57,
    },

    'مشيرب': {
        'variants': ['مشيرب', 'مشيرب 13'],
        'municipalities': ['الدوحة'],
        'total_n': 27,
        'notes': 'منطقة مشيرب التراثية في قلب الدوحة.',
    },

    'وادي السيل': {
        'variants': ['وادي السيل', 'وادي السيل 20'],
        'municipalities': ['الدوحة'],
        'total_n': 17,
    },

    'دفنة': {
        'variants': ['الدفنة', 'الدفنة 61'],
        'municipalities': ['الدوحة'],
        'total_n': 8,
        'notes': 'منطقة الدفنة على الكورنيش — أبراج عالية.',
    },

    'راس بو عبود': {
        'variants': ['راس بو عبود', 'راس بو عبود 28'],
        'municipalities': ['الدوحة'],
        'total_n': 6,
    },

    # ──────────────────────────────────────
    # NAMED VARIANTS (different names, same area)
    # ──────────────────────────────────────

    'مريخ': {
        'variants': ['مريخ', 'امريخ الجنوبي'],
        'municipalities': ['الريان'],
        'total_n': 295,
        'notes': (
            'مريخ و"امريخ الجنوبي" نفس المنطقة الجغرافية في الريان. '
            'الاختلاف في كتابة الاسم (بألف زائدة + إضافة "الجنوبي"). '
            'تحقق بالقرب الجغرافي: 2.2 كم بين المركزين. '
            'GIS أحياناً يصنف المرخ بـ TU والـ"امريخ الجنوبي" بـ R1.'
        ),
    },

    'الغرافة': {
        'variants': ['الغرافة', 'غرافة الريان'],
        'municipalities': ['الريان'],
        'total_n': 883,
        'notes': '"الغرافة" و"غرافة الريان" نفس المنطقة — اختلاف في الكتابة.',
    },

    'مدينة خليفة': {
        'variants': ['مدينة خليفة الجنوبية', 'مدينة خليفة الشمالية'],
        'municipalities': ['الدوحة'],
        'total_n': 506,
        'notes': (
            'مدينة خليفة منطقتان متجاورتان (شمالية وجنوبية). '
            'يمكن دمجهما إذا كان العقار قرب الحد بينهما. '
            'الفاصل: شارع جاسم بن حمد.'
        ),
    },

    'مرخية': {
        'variants': ['المرخية', 'حزم المرخية'],
        'municipalities': ['الدوحة', 'الريان'],
        'total_n': 192,
        'notes': '"المرخية" و"حزم المرخية" منطقة واحدة عملياً.',
    },

    'وادي لجمال': {
        'variants': ['وادي لجمال الشمالي', 'وادي لجمال الجنوبي'],
        'municipalities': ['الدوحة', 'الريان'],
        'total_n': 11,
        'notes': 'منطقتان متجاورتان شمالية وجنوبية — قابلتان للدمج.',
    },

    'لؤلؤة': {
        'variants': ['اللؤلؤة', 'جزيرة اللؤلؤة'],
        'municipalities': ['الدوحة'],
        'total_n': 117,
        'notes': (
            '"اللؤلؤة" و"جزيرة اللؤلؤة" نفس الجزيرة. '
            'تحفّظ: السوق سكني-تجاري مختلط (شقق وأبراج، ليست فلل).'
        ),
    },

    'مطار العتيق': {
        'variants': ['المطار العتيق', 'المطار'],
        'municipalities': ['الدوحة'],
        'total_n': 598,
        'notes': (
            '"المطار العتيق" هو الموقع السابق للمطار، تحوّل لأراضي سكنية. '
            '"المطار" بدون "العتيق" قد يشير لنفس المنطقة في بعض السجلات. '
            'تحفّظ: لا تدمجه مع "مطار الدوحة الدولي" — ذلك حمد الدولي الجديد.'
        ),
    },

    # ──────────────────────────────────────
    # AMBIGUOUS — DO NOT MERGE
    # ──────────────────────────────────────
    # هذه حالات تبدو متشابهة لكنها مناطق مختلفة فعلاً
    # نوثّقها لمنع دمجها بالخطأ
}


# ============================================================
# AREAS THAT SHOULD NOT BE MERGED (even if names are similar)
# ============================================================

DO_NOT_MERGE = {
    # ام صلال علي و ام صلال محمد منطقتان مختلفتان فعلاً
    ('ام صلال علي', 'ام صلال محمد'): 'منطقتان منفصلتان في أم صلال — متجاورتان لكن مختلفتان سعراً',

    # الريان الجديد ≠ الريان العتيق
    ('الريان الجديد', 'الريان العتيق'): 'العتيق هو الريان القديم، الجديد منطقة منفصلة',

    # المطار العتيق ≠ مطار الدوحة الدولي
    ('المطار العتيق', 'مطار الدوحة الدولي'): 'مطار الدوحة الدولي هو المطار الحالي (حمد الدولي)',

    # الوكير ≠ معيذر الوكير
    ('الوكير', 'معيذر الوكير'): 'معيذر الوكير منطقة فرعية صغيرة (n=27 فقط)',

    # ام قرن (أم صلال) ≠ ام قرن (الظعاين) — لكن لهما نفس الاسم!
    # ملاحظة: هذه الحالة معقدة. يحتاج فلتر بلدية إضافي.
}


# ============================================================
# PUBLIC API
# ============================================================

def get_all_aliases(area_name: str) -> List[str]:
    """
    احصل على كل الأسماء المرادفة لمنطقة معينة.

    Args:
        area_name: اسم المنطقة (أي شكل من الأشكال)

    Returns:
        قائمة كل الأسماء المكافئة. إذا لم تكن المنطقة في القاعدة،
        تُعاد القائمة بعنصر واحد (الاسم نفسه).

    Examples:
        >>> get_all_aliases('المعمورة')
        ['المعمورة', 'المعمورة 43', 'المعمورة 56']
        >>> get_all_aliases('امريخ الجنوبي')
        ['مريخ', 'امريخ الجنوبي']
        >>> get_all_aliases('الخيسة')
        ['الخيسة']  # غير موجودة، تُعاد كما هي
    """
    for canonical, info in ALIASES_DB.items():
        if area_name in info['variants']:
            return list(info['variants'])
    return [area_name]


def canonical_name(area_name: str) -> Optional[str]:
    """احصل على الاسم الأساسي (canonical) لمنطقة.

    Examples:
        >>> canonical_name('الثمامة 46')
        'ثمامة'
        >>> canonical_name('الخيسة')
        None  # not in DB
    """
    for canonical, info in ALIASES_DB.items():
        if area_name in info['variants']:
            return canonical
    return None


def get_municipalities(area_name: str) -> List[str]:
    """احصل على البلديات التي تتبعها المنطقة."""
    for canonical, info in ALIASES_DB.items():
        if area_name in info['variants']:
            return list(info['municipalities'])
    return []


def total_transactions(area_name: str) -> int:
    """العدد الإجمالي للمعاملات المرتبطة بالمنطقة وكل مرادفاتها."""
    for canonical, info in ALIASES_DB.items():
        if area_name in info['variants']:
            return info.get('total_n', 0)
    return 0


def is_alias_pair_blocked(area1: str, area2: str) -> Optional[str]:
    """
    يفحص هل دمج هاتين المنطقتين ممنوع صراحةً.

    Returns:
        سبب المنع (string) إذا ممنوع، None إذا مسموح.
    """
    for pair, reason in DO_NOT_MERGE.items():
        if (area1, area2) == pair or (area2, area1) == pair:
            return reason
    return None


def get_all_canonical_names() -> List[str]:
    """قائمة بكل الأسماء الأساسية في القاعدة."""
    return sorted(ALIASES_DB.keys())


# ============================================================
# CLI
# ============================================================

if __name__ == '__main__':
    import sys
    print(f"Qatar Area Aliases Database — {len(ALIASES_DB)} groups\n")

    if len(sys.argv) > 1:
        query = sys.argv[1]
        aliases = get_all_aliases(query)
        canonical = canonical_name(query)
        munis = get_municipalities(query)
        total = total_transactions(query)

        print(f"Query: '{query}'")
        print(f"Canonical: {canonical or '(not in DB)'}")
        print(f"All aliases: {aliases}")
        print(f"Municipalities: {munis}")
        print(f"Total transactions: {total}")
    else:
        # Show summary
        for canonical in sorted(ALIASES_DB.keys(),
                                 key=lambda x: -ALIASES_DB[x].get('total_n', 0)):
            info = ALIASES_DB[canonical]
            variants = ', '.join(info['variants'])
            total = info.get('total_n', 0)
            print(f"  {canonical:>20s} | n={total:>5d} | {variants}")

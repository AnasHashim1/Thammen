#!/usr/bin/env python3
"""
built_type.py — shared built-type classifier for COMPARABLE-POOL selection (Sprint 2.22.0a.12, A2).

Resolves the two live comp selectors onto ONE built-type taxonomy so the villa pool is no longer
contaminated by cheaper house / two-villa / compound rows, and so the `مسكن` split between the two
selectors (geo lumped مسكن→villa; bracket sent مسكن→dwelling) is reconciled.

Returns one of: 'LAND' | 'HOUSE' | 'STANDALONE_VILLA' | None   (None = excluded from every pool).

LOCKED decisions (post recon + multi-AI, 2026-05-31):
  1. فيلتان / فيلتين  → None (EXCLUDE)   — measured −6 to −10% discount vs single villa (distinct product)
  2. بنت هاوس         → STANDALONE_VILLA (FOLD)  — villa-range (+18%, far from apartment ~827/ft²)
  3. مجمع / فلل / count-words (ثلاث/أربع/خمس/ست) → None (EXCLUDE) — compound, LABEL-based
       (E20's 15K-m² area boundary stays SUBJECT-side in qatar_gis; it never touched comp rows)
  4. بيت / مسكن       → HOUSE   — removed from the villa pool (resolves the مسكن split)
  5. Subject-side classification is UNCHANGED (qatar_gis subtype mapping untouched) — A2 is
     comp-side stratification only; house-SUBJECT pooling defers to B (2.22.0b).

NOTE: these key on `نوع العقار` (TYPE), NBSP-normalized like the engine's _norm. They are orthogonal
to A1's `الاستخدام` (USAGE) residential filter — the two COMPOSE (a comp row must pass BOTH).
"""
import re

# Order matters: most specific / exclusion tokens first.
_COMMERCIAL_TOKENS = ('عمارة', 'برج', 'شقة', 'مبنى', 'محل', 'مكتب', 'اداري', 'إداري',
                      'مستودع', 'مخزن', 'مصنع', 'فندق', 'مدرسة', 'مسجد', 'سوق', 'معرض', 'تجاري')
_COMPOUND_COUNT_WORDS = ('ثلاث', 'اربع', 'أربع', 'خمس', 'ست ', 'ستة', 'سبع', 'فلل')


def _norm(s) -> str:
    return re.sub(r'\s+', ' ', str(s or '')).strip()


def built_type(row) -> 'str | None':
    """Classify a MoJ row's `نوع العقار` into a comp-pool built-type stratum (or None = excluded)."""
    t = _norm(row.get('نوع العقار', ''))
    if not t:
        return None
    if 'قصر' in t:                                   # palace — excluded
        return None
    if any(x in t for x in _COMMERCIAL_TOKENS):       # apartment / commercial — excluded
        return None
    if t == 'أرض فضاء':                               # LAND (exact, like both legacy categorizers)
        return 'LAND'
    # COMPOUND (multi-villa) — LABEL-based exclusion (LOCK 3). Before the villa branch.
    if 'مجمع' in t or any(x in t for x in _COMPOUND_COUNT_WORDS):
        return None
    # فيلتان (2-villa) — EXCLUDE (LOCK 1; measured discount product).
    if 'فيلتان' in t or 'فيلتين' in t:
        return None
    # بنت هاوس (penthouse) — FOLD into the villa stratum (LOCK 2). Before house, after compound.
    if 'بنت هاوس' in t:
        return 'STANDALONE_VILLA'
    # HOUSE = بيت / مسكن (LOCK 4 — resolves the split; removed from the villa pool).
    if 'بيت' in t or 'مسكن' in t:
        return 'HOUSE'
    # Single villa (فيلا + its ملحق/مجلس/دور أرضي/طابقين variants).
    if 'فيلا' in t:
        return 'STANDALONE_VILLA'
    return None


# Map the comp selectors' coarse `category` arg to the built-type pool they should gather.
# 'villa' comp category → the pure STANDALONE_VILLA stratum (house/فيلتان/compound now excluded).
_CATEGORY_TO_BUILT_TYPE = {
    'villa': 'STANDALONE_VILLA',
    'land': 'LAND',
}


def matches_category(row, category: str) -> bool:
    """True if `row` belongs in the comp pool for the given coarse `category` ('villa'|'land').

    For categories with no built-type stratum (palace/compound/all/None), the caller keeps its
    legacy behaviour — this helper is only consulted for 'villa' and 'land'.
    """
    target = _CATEGORY_TO_BUILT_TYPE.get(category)
    if target is None:
        return True   # non-stratified category: defer to caller's legacy categorizer
    return built_type(row) == target

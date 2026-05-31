#!/usr/bin/env python3
"""
usage_filter.py — residential-usage whitelist for the VILLA comparable pool.

Sprint 2.22.0a.11 (A1). The MoJ `الاستخدام` (usage) column carried non-residential rows
(commercial / apartment-complex / farm / school / office) into the villa comparable pool —
priced ~+101% above residential — which inflated the villa median ~5% (Phase-1b / RISK_REGISTER R8).

This is a WHITELIST (robust to the ~40 spelling variants of the usage labels):
  - KEEP blank usage (blank rows price like residential, +5% vs the residential median, NOT like
    the +101% non-residential contamination — Phase-1b item 4).
  - KEEP the residential whitelist below.
  - EXCLUDE everything else by default — incl. `عمارات او مجمعات سكنية` (apartment/complex) and all
    commercial / farm / school / office labels and their misspellings.

NOTE: these are `الاستخدام` (USAGE) values, NOT `نوع العقار` (TYPE). The type categorizers
(`moj_reference.categorize` / `geo_reference_v2._categorize`) are UNCHANGED — the `مسكن` *type*
divergence between them is a separate item (A2), out of A1 scope. Applies to the VILLA pool ONLY;
land-usage filtering is out of A1 scope.
"""
import re

# `الاستخدام` (usage) values treated as residential for the villa pool.
_RESIDENTIAL_USAGES = {
    'فلل او بيوت سكنية',      # villas / residential houses (primary; n≈18.6k)
    'مسكن',                   # dwelling
    'مساكن كبار الموظفين',    # senior-staff housing
}


def _is_residential_usage(row) -> bool:
    """True if the row's `الاستخدام` is blank (KEEP) or in the residential whitelist; else False.

    Normalization matches the engine's `_norm` (re.sub(r'\\s+',' ',s).strip()), so NBSP/space
    variants of the whitelisted labels are handled.
    """
    u = re.sub(r'\s+', ' ', str(row.get('الاستخدام', '') or '')).strip()
    return u == '' or u in _RESIDENTIAL_USAGES

#!/usr/bin/env python3
"""
rent_reference.py — Build rental market reference from government transaction data.

Data source:
    XLSX files downloaded from qrep.aqarat.gov.qa
    "قائمة معاملات الإيجار" — yearly files, 2023-2026+

Columns (row 2 = headers):
    البلدية | عدد الغرف | نوع الوحدة | قيمة الإيجار | حالة العقد | تاريخ التوثيق | تاريخ بداية العقد | تاريخ نهاية العقد

Coverage: ~360,000 transactions (2023-2026)
Limitation: Municipality only — no sub-area. System MUST disclose this.

Usage:
    python3 rent_reference.py <xlsx_dir>
    python3 rent_reference.py /path/to/rental/xlsx/files

    # programmatic
    from rent_reference import build_rent_reference, query_rent
    ref = build_rent_reference('/path/to/xlsx/dir')
    result = query_rent(ref, municipality='الدوحة', unit_type='شقة', rooms=2)
"""

import json
import re
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, List, Tuple

try:
    import openpyxl
    _OPENPYXL = True
except ImportError:
    _OPENPYXL = False

# ============================================================
# CONSTANTS
# ============================================================

DEFAULT_WINDOW_MONTHS = 24
FALLBACK_WINDOW_MONTHS = 36
MIN_N = 20
MIN_N_INDICATIVE = 10
MIN_N_BOUND = 5

# Room groupings — collapse extremes
ROOM_BRACKETS = {
    0: 'studio',      # 0 = استوديو or محل
    1: '1BR',
    2: '2BR',
    3: '3BR',
    4: '4BR',
    5: '5BR',
    6: '6BR+',
    7: '6BR+',
    8: '6BR+',
    9: '6BR+',
    10: '6BR+',
}

# Unit type normalization
UNIT_TYPE_MAP = {
    'شقة':           'apartment',
    'فيلا':          'villa',
    'معرض تجاري / محل': 'retail',
    'محل':           'retail',
    'مكتب':          'office',
    'عمارة':         'building',
    'مجمع تجاري':    'commercial_complex',
    'مجمع سكني':     'residential_complex',
    'مبنى إداري':    'admin_building',
    'برج':           'tower',
    'أخرى':          'other',
    '---':           'unknown',
}

# Municipality normalization (ensure consistency)
MUNICIPALITY_NORMALIZE = {
    'الدوحة': 'الدوحة',
    'الريان': 'الريان',
    'الوكرة': 'الوكرة',
    'الظعاين': 'الظعاين',
    'أم صلال': 'أم صلال',
    'الخور والذخيرة': 'الخور والذخيرة',
    'الشمال': 'الشمال',
    'الشيحانية': 'الشيحانية',
}


def normalize(s):
    return re.sub(r'\s+', ' ', str(s or '')).strip()


def parse_date(s):
    if not s or s == '---':
        return None
    try:
        return datetime.strptime(str(s).strip(), '%Y-%m-%d')
    except (ValueError, TypeError):
        return None


def to_int(v):
    try:
        return int(v)
    except (ValueError, TypeError):
        return None


def to_float(v):
    try:
        return float(str(v).replace(',', '').strip())
    except (ValueError, TypeError):
        return None


def room_bracket(rooms):
    if rooms is None:
        return None
    r = to_int(rooms)
    if r is None:
        return None
    return ROOM_BRACKETS.get(r, '6BR+' if r >= 6 else None)


def unit_type_key(raw_type):
    t = normalize(raw_type)
    return UNIT_TYPE_MAP.get(t, 'other')


def median_of(values):
    s = sorted(v for v in values if v is not None and v > 0)
    if not s:
        return None
    return s[len(s) // 2]


def quartile_stats(values):
    """Compute quartile statistics for a list of numeric values."""
    values = sorted(v for v in values if v is not None and v > 0)
    if not values:
        return None
    n = len(values)
    p = lambda q: values[int(q * (n - 1))]
    return {
        'n': n,
        'min': round(values[0]),
        'p25': round(p(0.25)),
        'median': round(p(0.50)),
        'p75': round(p(0.75)),
        'max': round(values[-1]),
    }


def confidence_label(n):
    """Return confidence label based on sample size."""
    if n >= MIN_N:
        return 'reliable'
    elif n >= MIN_N_INDICATIVE:
        return 'indicative'
    elif n >= MIN_N_BOUND:
        return 'bound_only'
    else:
        return 'insufficient'


# ============================================================
# DATA LOADING
# ============================================================

def load_rental_xlsx(xlsx_path: str) -> List[dict]:
    """Load rental transactions from a single XLSX file."""
    if not _OPENPYXL:
        raise ImportError("openpyxl required: pip install openpyxl")

    wb = openpyxl.load_workbook(xlsx_path, read_only=True, data_only=True)
    ws = wb.active
    records = []

    for i, row in enumerate(ws.iter_rows(min_row=3, values_only=True)):
        # Skip empty rows
        if not row or not row[0]:
            continue
        muni, rooms, unit_type, rent, contract_state, doc_date, start_date, end_date = row[:8]

        rent_val = to_float(rent)
        if rent_val is None or rent_val <= 0:
            continue

        doc_dt = parse_date(doc_date)
        start_dt = parse_date(start_date)
        end_dt = parse_date(end_date)

        # Contract duration (months) for annual rent estimation
        duration_months = None
        if start_dt and end_dt and end_dt > start_dt:
            duration_months = round((end_dt - start_dt).days / 30.44)

        muni_norm = MUNICIPALITY_NORMALIZE.get(normalize(muni), normalize(muni))

        records.append({
            'municipality': muni_norm,
            'rooms': to_int(rooms),
            'room_bracket': room_bracket(rooms),
            'unit_type_ar': normalize(unit_type),
            'unit_type': unit_type_key(unit_type),
            'rent_monthly': rent_val,
            'contract_state': normalize(contract_state),
            'doc_date': doc_dt,
            'start_date': start_dt,
            'end_date': end_dt,
            'duration_months': duration_months,
        })

    wb.close()
    return records


def load_all_rental_xlsx(xlsx_dir: str) -> List[dict]:
    """Load all rental XLSX files from a directory."""
    d = Path(xlsx_dir)
    files = sorted(d.glob('*إيجار*.xlsx')) + sorted(d.glob('*rent*.xlsx'))
    if not files:
        # Try parent or exact paths
        files = sorted(d.glob('*.xlsx'))
        files = [f for f in files if 'إيجار' in f.name or 'rent' in f.name.lower()]

    all_records = []
    for f in files:
        print(f"  Loading {f.name}...", end=' ', flush=True)
        recs = load_rental_xlsx(str(f))
        print(f"{len(recs):,} records")
        all_records.extend(recs)

    print(f"  Total: {len(all_records):,} rental transactions")
    return all_records


# ============================================================
# REFERENCE BUILDING
# ============================================================

def build_rent_reference(
    xlsx_dir: str = None,
    records: List[dict] = None,
    window_months: int = DEFAULT_WINDOW_MONTHS,
    ref_date: datetime = None,
) -> dict:
    """
    Build rental reference from XLSX files or pre-loaded records.

    Returns a nested dict:
        {municipality → {unit_type → {room_bracket → stats}}}

    Each stats dict contains:
        n, min, p25, median, p75, max, confidence, window, caveats
    """
    if records is None:
        if xlsx_dir is None:
            raise ValueError("Provide xlsx_dir or records")
        records = load_all_rental_xlsx(xlsx_dir)

    if ref_date is None:
        # Use the latest doc_date as reference
        dates = [r['doc_date'] for r in records if r['doc_date']]
        ref_date = max(dates) if dates else datetime.now()

    cutoff = ref_date - timedelta(days=window_months * 30.44)
    fallback_cutoff = ref_date - timedelta(days=FALLBACK_WINDOW_MONTHS * 30.44)

    # Group records
    groups = defaultdict(list)
    for r in records:
        if r['unit_type'] in ('unknown', 'other'):
            continue
        if r['room_bracket'] is None:
            continue
        key = (r['municipality'], r['unit_type'], r['room_bracket'])
        groups[key].append(r)

    reference = {}
    metadata = {
        'ref_date': ref_date.strftime('%Y-%m-%d'),
        'window_months': window_months,
        'total_records': len(records),
        'municipalities': set(),
        'unit_types': set(),
        'generated': datetime.now().strftime('%Y-%m-%d %H:%M'),
        'source': 'qrep.aqarat.gov.qa — قائمة معاملات الإيجار',
        'limitation': 'بلدية فقط — لا منطقة فرعية. الإيجار الفعلي يختلف حسب المنطقة داخل البلدية.',
    }

    for (muni, utype, rbracket), recs in groups.items():
        # Try primary window
        filtered = [r for r in recs if r['doc_date'] and r['doc_date'] >= cutoff]
        used_window = window_months

        if len(filtered) < MIN_N:
            # Fallback to wider window
            filtered = [r for r in recs if r['doc_date'] and r['doc_date'] >= fallback_cutoff]
            used_window = FALLBACK_WINDOW_MONTHS

        rents = [r['rent_monthly'] for r in filtered]
        stats = quartile_stats(rents)

        if stats is None or stats['n'] < MIN_N_BOUND:
            continue

        conf = confidence_label(stats['n'])
        stats['confidence'] = conf
        stats['window_months'] = used_window
        stats['contract_mix'] = {
            'new': sum(1 for r in filtered if r['contract_state'] == 'جديد'),
            'renewal': sum(1 for r in filtered if r['contract_state'] == 'تجديد'),
        }

        # Caveats
        caveats = []
        if conf == 'indicative':
            caveats.append(f'عينة محدودة (n={stats["n"]}). الوسيط إرشادي فقط.')
        elif conf == 'bound_only':
            caveats.append(f'عينة صغيرة جداً (n={stats["n"]}). للاسترشاد فقط كحدود.')
        if used_window > DEFAULT_WINDOW_MONTHS:
            caveats.append(f'نافذة موسَّعة {used_window} شهر (العينة في 24 شهر < {MIN_N}).')
        caveats.append('البيانات على مستوى البلدية — الإيجارات تختلف حسب المنطقة الفرعية.')
        stats['caveats'] = caveats

        # Store
        if muni not in reference:
            reference[muni] = {}
        if utype not in reference[muni]:
            reference[muni][utype] = {}
        reference[muni][utype][rbracket] = stats

        metadata['municipalities'].add(muni)
        metadata['unit_types'].add(utype)

    # Convert sets to sorted lists for JSON
    metadata['municipalities'] = sorted(metadata['municipalities'])
    metadata['unit_types'] = sorted(metadata['unit_types'])
    metadata['groups_built'] = sum(
        len(rbrackets)
        for utypes in reference.values()
        for rbrackets in utypes.values()
    )

    return {'reference': reference, 'metadata': metadata}


# ============================================================
# QUERYING
# ============================================================

def query_rent(
    ref: dict,
    municipality: str,
    unit_type: str = 'apartment',
    rooms: int = None,
    room_bracket: str = None,
) -> Optional[dict]:
    """
    Query the rental reference for a specific combination.

    Args:
        ref: output of build_rent_reference()
        municipality: بلدية name (e.g. 'الدوحة')
        unit_type: 'apartment'/'villa'/'office'/'retail'
        rooms: number of rooms (will be mapped to bracket)
        room_bracket: direct bracket key (e.g. '2BR')

    Returns:
        dict with n, median, p25, p75, confidence, caveats
        or None if not found
    """
    data = ref.get('reference', ref)
    muni_data = data.get(municipality)
    if not muni_data:
        return None

    type_data = muni_data.get(unit_type)
    if not type_data:
        return None

    if room_bracket is None and rooms is not None:
        room_bracket = ROOM_BRACKETS.get(rooms, '6BR+' if rooms >= 6 else None)

    if room_bracket and room_bracket in type_data:
        result = dict(type_data[room_bracket])
        result['municipality'] = municipality
        result['unit_type'] = unit_type
        result['room_bracket'] = room_bracket
        return result

    # If specific bracket not found, try adjacent
    return None


def estimate_annual_rent(
    ref: dict,
    municipality: str,
    unit_type: str = 'apartment',
    rooms: int = None,
    room_bracket: str = None,
) -> Optional[dict]:
    """
    Estimate annual rent for income approach.

    Returns dict with:
        monthly_median, annual_median, n, confidence, caveats,
        annual_range (p25*12, p75*12)
    """
    q = query_rent(ref, municipality, unit_type, rooms, room_bracket)
    if q is None:
        return None

    return {
        'monthly_median': q['median'],
        'annual_median': q['median'] * 12,
        'annual_low': q['p25'] * 12,
        'annual_high': q['p75'] * 12,
        'n': q['n'],
        'confidence': q['confidence'],
        'window_months': q.get('window_months'),
        'municipality': municipality,
        'unit_type': unit_type,
        'room_bracket': q.get('room_bracket'),
        'caveats': q.get('caveats', []),
        'source': 'qrep.aqarat.gov.qa — قائمة معاملات الإيجار',
        'limitation': 'بلدية فقط — لا منطقة فرعية',
    }


def estimate_villa_rent(
    ref: dict,
    municipality: str,
    bedrooms: int = 5,
) -> Optional[dict]:
    """Convenience: estimate rent for a villa."""
    return estimate_annual_rent(ref, municipality, 'villa', rooms=bedrooms)


def estimate_apartment_rent(
    ref: dict,
    municipality: str,
    bedrooms: int = 2,
) -> Optional[dict]:
    """Convenience: estimate rent for an apartment."""
    return estimate_annual_rent(ref, municipality, 'apartment', rooms=bedrooms)


# ============================================================
# INCOME APPROACH VALUATION
# ============================================================

def income_approach_value(
    annual_rent: float,
    cap_rate: float = 0.065,
    service_charge_annual: float = 0,
    vacancy_pct: float = 0.085,
    maintenance_pct: float = 0.005,
    management_pct: float = 0.0,
    property_value_for_maintenance: float = None,
) -> dict:
    """
    Compute property value using income (capitalization) approach.

    NOI = Gross Rent - (Service Charge + Vacancy + Maintenance + Management)
    Value = NOI / Cap Rate

    Args:
        annual_rent: gross annual rent
        cap_rate: capitalization rate (default 6.5% — Qatar market)
        service_charge_annual: total annual service charges
        vacancy_pct: vacancy allowance as fraction of gross rent
        maintenance_pct: maintenance as fraction of property value (iterative)
        management_pct: management fee as fraction of gross rent
        property_value_for_maintenance: if None, uses iterative solve

    Returns:
        dict with value, noi, costs breakdown, sensitivity
    """
    vacancy = annual_rent * vacancy_pct
    management = annual_rent * management_pct

    # Maintenance is % of value — need iterative solve if value unknown
    if property_value_for_maintenance is None:
        # First pass: estimate without maintenance
        noi_est = annual_rent - service_charge_annual - vacancy - management
        value_est = noi_est / cap_rate if cap_rate > 0 else 0
        # Second pass: with maintenance
        maintenance = value_est * maintenance_pct
        noi = noi_est - maintenance
        value = noi / cap_rate if cap_rate > 0 else 0
        # Third pass: refine
        maintenance = value * maintenance_pct
        noi = annual_rent - service_charge_annual - vacancy - management - maintenance
        value = noi / cap_rate if cap_rate > 0 else 0
    else:
        maintenance = property_value_for_maintenance * maintenance_pct
        noi = annual_rent - service_charge_annual - vacancy - management - maintenance
        value = noi / cap_rate if cap_rate > 0 else 0

    costs_total = service_charge_annual + vacancy + maintenance + management
    opex_ratio = costs_total / annual_rent if annual_rent > 0 else 0

    # Sensitivity: ±0.5% cap rate, ±20% service charge
    sensitivity = {}
    for cr_label, cr in [('-0.5%', cap_rate - 0.005), ('+0.5%', cap_rate + 0.005)]:
        if cr > 0:
            sensitivity[f'cap_rate {cr_label}'] = round(noi / cr)
    for sc_label, sc_mult in [('-20%', 0.8), ('+20%', 1.2)]:
        sc_adj = service_charge_annual * sc_mult
        noi_adj = annual_rent - sc_adj - vacancy - maintenance - management
        if cap_rate > 0:
            sensitivity[f'service_charge {sc_label}'] = round(noi_adj / cap_rate)

    return {
        'income_value': round(value),
        'annual_gross_rent': round(annual_rent),
        'noi': round(noi),
        'cap_rate_used': cap_rate,
        'costs': {
            'service_charge': round(service_charge_annual),
            'vacancy': round(vacancy),
            'maintenance': round(maintenance),
            'management': round(management),
            'total': round(costs_total),
        },
        'opex_ratio': round(opex_ratio, 3),
        'gross_yield_pct': round(annual_rent / value * 100, 2) if value > 0 else None,
        'net_yield_pct': round(noi / value * 100, 2) if value > 0 else None,
        'sensitivity': sensitivity,
    }


# ============================================================
# CLI
# ============================================================

def print_summary(ref_data):
    """Print human-readable summary of rental reference."""
    meta = ref_data['metadata']
    ref = ref_data['reference']

    print(f"\n{'=' * 70}")
    print(f"  Rental Reference — {meta['ref_date']}")
    print(f"  Window: {meta['window_months']} months")
    print(f"  Total records: {meta['total_records']:,}")
    print(f"  Groups built: {meta['groups_built']}")
    print(f"  Source: {meta['source']}")
    print(f"  ⚠️ {meta['limitation']}")
    print(f"{'=' * 70}")

    for muni in sorted(ref.keys()):
        print(f"\n  📍 {muni}")
        for utype in sorted(ref[muni].keys()):
            print(f"    {utype}:")
            for rb in sorted(ref[muni][utype].keys()):
                s = ref[muni][utype][rb]
                conf_icon = {'reliable': '✅', 'indicative': '⚠️',
                             'bound_only': '🔶', 'insufficient': '❌'}
                icon = conf_icon.get(s['confidence'], '?')
                print(f"      {rb:>6s}: median {s['median']:>7,} QAR  "
                      f"(p25={s['p25']:,}, p75={s['p75']:,})  "
                      f"n={s['n']:>5}  {icon} {s['confidence']}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 rent_reference.py <xlsx_dir_or_file> [output.json]")
        sys.exit(1)

    source = sys.argv[1]
    output = sys.argv[2] if len(sys.argv) > 2 else 'rent_reference.json'

    p = Path(source)
    if p.is_dir():
        ref_data = build_rent_reference(xlsx_dir=str(p))
    elif p.is_file() and p.suffix == '.xlsx':
        recs = load_rental_xlsx(str(p))
        ref_data = build_rent_reference(records=recs)
    else:
        print(f"Error: {source} is not a directory or XLSX file")
        sys.exit(1)

    print_summary(ref_data)

    with open(output, 'w', encoding='utf-8') as f:
        json.dump(ref_data, f, ensure_ascii=False, indent=2, default=str)
    print(f"\n  Saved to {output}")


if __name__ == '__main__':
    main()

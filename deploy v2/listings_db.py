#!/usr/bin/env python3
"""
listings_db.py — جمع الإعلانات النشطة من المواقع العقارية وحساب وسيط
                  مرجّح بعمر الإعلان وفق منهجية RICS.

المنهجية:
    وزن العمر:
        0-90 يوم    → 1.0  (المنطقة الذهبية — السوق القطري أبطأ من العالمي)
        90-180 يوم  → 0.5  (انتقالية — السوق بدأ يرفض السعر)
        180-365 يوم → 0.2  (متأخرة — حد أعلى فقط)
        365+ يوم    → استبعاد

    عند غياب العمر: يُفترض 60 يوم (وزن 0.6)

    خصم الإعلان: الإعلانات تنحف بنسبة 10-15% للوصول للمعاملة الفعلية.

المصادر المدعومة:
    - arady.qa (الصفحة الأولى — متاحة كاملة)
    - PropertyFinder QA (يحتاج تكامل منفصل)

الاستخدام:
    from listings_db import fetch_active_listings, weighted_listings_median

    listings = fetch_active_listings(area='مريخ', property_type='villa',
                                     min_area=490, max_area=736)
    result = weighted_listings_median(listings)
"""

import re
import gzip
import ssl
import urllib.parse
import urllib.request
from typing import List, Dict, Optional


# ============================================================
# CONSTANTS
# ============================================================

# Age weighting (RICS methodology, calibrated for Qatar)
AGE_WEIGHTS = [
    (90,   1.0,  'gold',         'منطقة ذهبية — حديث جداً'),
    (180,  0.5,  'transitional', 'انتقالية — السوق بدأ يرفض السعر'),
    (365,  0.2,  'late',         'متأخرة — حد أعلى فقط'),
]
DEFAULT_AGE = 60       # If age not detected
EXCLUDE_AFTER = 365    # Days after which listing is fully excluded

# Listing-to-transaction discount (typical Qatar: 10-15%)
LISTING_DISCOUNT = 0.13

# User agent
USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0'


# ============================================================
# HTTP UTILITIES
# ============================================================

def _make_ssl_ctx():
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


def _fetch(url: str, timeout: int = 20) -> Optional[str]:
    """Fetch URL with proper headers, gzip handling."""
    req = urllib.request.Request(url, headers={
        'User-Agent': USER_AGENT,
        'Accept': 'text/html,application/xhtml+xml',
        'Accept-Language': 'ar,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate',
    })
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=_make_ssl_ctx()) as resp:
            data = resp.read()
            if resp.headers.get('Content-Encoding') == 'gzip':
                data = gzip.decompress(data)
            return data.decode('utf-8', errors='replace')
    except Exception:
        return None


# ============================================================
# AGE PARSING
# ============================================================

def parse_arabic_age(text: str) -> Optional[int]:
    """Convert Arabic relative time to days. Returns None if not found."""
    if 'الآن' in text and re.search(r'\d+\s+(?:دقيقة|دقائق|ساعة|ساعات)\s+الآن\s*$', text):
        return 0  # Listed today

    m = re.search(
        r'(\d+)\s+(يوم|أيام|أسبوع|أسابيع|شهر|أشهر|سنة|سنوات|ساعة|ساعات|دقيقة|دقائق)'
        r'\s+الآن\s*$',
        text
    )
    if not m:
        return None

    n = int(m.group(1))
    unit = m.group(2)

    if unit in ('يوم', 'أيام'):
        return n
    if unit in ('أسبوع', 'أسابيع'):
        return n * 7
    if unit in ('شهر', 'أشهر'):
        return n * 30
    if unit in ('سنة', 'سنوات'):
        return n * 365
    # hours/minutes = today
    return 0


def get_age_weight(age_days: Optional[int]) -> tuple:
    """
    Return (weight, tier_name, label) for a given age.

    age_days=None → unknown — assume DEFAULT_AGE (60 days, weight ~0.8)
    age_days >= EXCLUDE_AFTER → weight 0
    """
    if age_days is None:
        # Unknown age: use a conservative default tier
        return (0.7, 'unknown', 'عمر غير محدد — افتراض متحفظ')
    if age_days < 0:
        age_days = 0

    if age_days >= EXCLUDE_AFTER:
        return (0.0, 'excluded', 'مستبعد — أكثر من سنة')

    for max_days, weight, tier, label in AGE_WEIGHTS:
        if age_days <= max_days:
            return (weight, tier, label)

    return (0.0, 'excluded', 'مستبعد')


# ============================================================
# ARADY.QA PARSER
# ============================================================

def fetch_arady_listings(
    category: str = 'villas',
    search_query: Optional[str] = None,
) -> List[Dict]:
    """
    Fetch arady.qa listings. Currently only page 1 is accessible
    (pages 2+ are JavaScript-rendered and blocked).

    Args:
        category: 'villas' or 'lands'
        search_query: optional Arabic query (e.g., 'مريخ') to filter results

    Returns list of dicts with: url, type, location, area_m2, price,
                                 price_m2, price_ft, age_days, weight.
    """
    base_url = f'https://arady.qa/ar/listings/{category}'
    if search_query:
        url = f'{base_url}?q={urllib.parse.quote(search_query)}'
    else:
        url = base_url

    html = _fetch(url)
    if not html:
        return []

    # Each property has 2 link entries (image + content). Dedupe by ID.
    cards = re.findall(
        r'<a[^>]*href="(/ar/property/(\d+))"[^>]*>(.*?)</a>',
        html, re.S
    )

    seen = set()
    unique_cards = []
    for url_path, pid, content in cards:
        if pid in seen:
            continue
        seen.add(pid)
        unique_cards.append((pid, url_path, content))

    listings = []
    for pid, url_path, content in unique_cards:
        listing = _parse_arady_card_html(content)
        if not listing:
            continue

        listing['source'] = 'arady.qa'
        listing['id'] = pid
        listing['url'] = f'https://arady.qa{url_path}'
        listings.append(listing)

    return listings


def _parse_arady_card_html(html: str) -> Optional[Dict]:
    """
    Parse an arady listing card from RAW HTML (not stripped text).

    arady displays time in distinct HTML elements:
    - First time block = listing age (e.g., "22 يوم")
    - Second time block = last refresh (e.g., "3 دقائق")

    If only one block exists and uses minute/hour units, listing is fresh.
    """
    out = {}

    # Strip HTML for text extraction of price/area/location
    text = re.sub(r'<[^>]+>', ' ', html)
    text = re.sub(r'\s+', ' ', text).strip()

    # Price (e.g., "5,000,000 ريال" — first occurrence)
    m = re.search(r'([\d,]+)\s*ريال', text)
    if not m:
        return None
    out['price'] = float(m.group(1).replace(',', ''))

    # Property type
    m = re.search(r'(فيلا\s*\w*|أرض\s*\w*|بيت\s*\w*|قصر|مجمع\s*\w*|شقة)', text)
    out['type'] = m.group(1).strip() if m else 'unknown'

    # Bedrooms
    m = re.search(r'(\d+)\s*غرف\s*نوم', text)
    if m:
        out['bedrooms'] = int(m.group(1))

    # Location (after "للبيع في")
    m = re.search(r'للبيع\s+في\s+(\S+(?:\s+\S+)?)', text)
    if m:
        loc = m.group(1).strip()
        loc = re.sub(r'\s+\d+\s*$', '', loc)  # strip trailing digits
        out['location'] = loc

    # Area (e.g., "658 متر مربع")
    m = re.search(r'([\d,]+)\s*متر\s+مربع', text)
    if not m:
        return None
    out['area_m2'] = float(m.group(1).replace(',', ''))

    # Foot price (right after "متر مربع")
    m = re.search(r'متر\s+مربع\s+([\d,]+)', text)
    if m:
        out['price_ft_listed'] = float(m.group(1).replace(',', ''))

    # Compute price/m²
    if out.get('price') and out.get('area_m2') and out['area_m2'] > 0:
        out['price_m2'] = out['price'] / out['area_m2']
        out['price_ft'] = out['price_m2'] / 10.764

    # ── Age extraction from HTML elements ──
    # Find all time-bearing HTML elements
    time_blocks = re.findall(
        r'<(?:time|span|div|p)[^>]*>\s*([^<]*?\d+\s+'
        r'(?:يوم|أيام|أسبوع|أسابيع|شهر|أشهر|سنة|سنوات|ساعة|ساعات|دقيقة|دقائق)'
        r'[^<]*?)\s*</',
        html
    )

    age_days = None
    for block in time_blocks:
        block = block.strip()
        # Try to find day/week/month/year (LISTING AGE)
        m = re.search(r'(\d+)\s+(يوم|أيام|أسبوع|أسابيع|شهر|أشهر|سنة|سنوات)', block)
        if m:
            n = int(m.group(1))
            unit = m.group(2)
            if unit in ('يوم', 'أيام'):
                age_days = n
            elif unit in ('أسبوع', 'أسابيع'):
                age_days = n * 7
            elif unit in ('شهر', 'أشهر'):
                age_days = n * 30
            elif unit in ('سنة', 'سنوات'):
                age_days = n * 365
            break

    # If no day/week/month/year found, but we have minute/hour blocks,
    # the listing is fresh (< 1 day)
    if age_days is None:
        for block in time_blocks:
            if re.search(r'\d+\s+(?:ساعة|ساعات|دقيقة|دقائق)', block):
                age_days = 0
                break

    out['age_days'] = age_days  # may be None if not detected

    # Apply age weight
    weight, tier, label = get_age_weight(age_days)
    out['weight'] = weight
    out['age_tier'] = tier
    out['age_label'] = label

    return out


def _parse_arady_card(text: str) -> Optional[Dict]:
    """DEPRECATED — use _parse_arady_card_html instead."""
    return None


# ============================================================
# AGGREGATION
# ============================================================

def filter_listings(
    listings: List[Dict],
    area: Optional[str] = None,
    property_type: Optional[str] = None,
    min_area: Optional[float] = None,
    max_area: Optional[float] = None,
    max_age_days: int = EXCLUDE_AFTER,
) -> List[Dict]:
    """Filter listings by area name (substring match), type, size, age."""
    out = []
    for lst in listings:
        if area and area not in lst.get('location', ''):
            # Try removing definite article from query
            area_no_al = re.sub(r'^ال', '', area)
            loc_no_al = re.sub(r'^ال', '', lst.get('location', ''))
            if area_no_al not in loc_no_al and loc_no_al not in area_no_al:
                continue
        if property_type and property_type not in lst.get('type', ''):
            if not (property_type == 'villa' and 'فيلا' in lst.get('type', '')):
                continue
        if min_area and lst.get('area_m2', 0) < min_area:
            continue
        if max_area and lst.get('area_m2', 0) > max_area:
            continue
        if lst.get('age_days') is not None and lst['age_days'] >= max_age_days:
            continue
        out.append(lst)
    return out


def weighted_listings_median(listings: List[Dict]) -> Dict:
    """
    Compute weighted median using age-based weights.

    Returns:
        {
            'n': int,                       # raw count
            'effective_n': float,           # sum of weights
            'weighted_median_m2': float,    # weighted median price/m²
            'weighted_median_ft': float,
            'estimated_market_m2': float,   # after listing discount
            'tier_breakdown': {tier: count},
            'discount_applied': float,
            'oldest_days': int,
            'newest_days': int,
        }
    """
    valid = [l for l in listings if l.get('weight', 0) > 0 and l.get('price_m2')]
    if not valid:
        return {'n': 0, 'effective_n': 0, 'weighted_median_m2': None}

    # Build (price, weight) pairs
    pairs = [(l['price_m2'], l['weight']) for l in valid]

    # Weighted median
    pairs.sort(key=lambda x: x[0])
    total_w = sum(w for _, w in pairs)
    cumulative = 0
    weighted_med = pairs[-1][0]
    for val, w in pairs:
        cumulative += w
        if cumulative >= total_w / 2:
            weighted_med = val
            break

    # Tier breakdown
    tier_count = {}
    for l in valid:
        t = l.get('age_tier', 'unknown')
        tier_count[t] = tier_count.get(t, 0) + 1

    # Apply listing-to-transaction discount
    estimated_market = weighted_med * (1 - LISTING_DISCOUNT)

    ages = [l['age_days'] for l in valid if l.get('age_days') is not None]

    return {
        'n': len(valid),
        'effective_n': round(total_w, 1),
        'weighted_median_m2': round(weighted_med),
        'weighted_median_ft': round(weighted_med / 10.764),
        'estimated_market_m2': round(estimated_market),
        'estimated_market_ft': round(estimated_market / 10.764),
        'tier_breakdown': tier_count,
        'discount_applied': LISTING_DISCOUNT,
        'oldest_days': max(ages) if ages else None,
        'newest_days': min(ages) if ages else None,
        'min_price_m2': round(min(p for p, _ in pairs)),
        'max_price_m2': round(max(p for p, _ in pairs)),
    }


def fetch_active_listings(
    area: Optional[str] = None,
    property_type: str = 'villa',
    min_area: Optional[float] = None,
    max_area: Optional[float] = None,
    max_age_days: int = EXCLUDE_AFTER,
) -> List[Dict]:
    """
    High-level: fetch + filter listings from all sources.

    Currently uses arady.qa only. Can be extended with PropertyFinder, Mzad.
    """
    all_listings = []

    # arady.qa villas — pass area as search query for better results
    if property_type in ('villa', 'all'):
        all_listings.extend(fetch_arady_listings('villas', search_query=area))

    # arady.qa lands
    if property_type in ('land', 'all'):
        all_listings.extend(fetch_arady_listings('lands', search_query=area))

    # Filter
    return filter_listings(
        all_listings,
        area=area,
        property_type=property_type,
        min_area=min_area,
        max_area=max_area,
        max_age_days=max_age_days,
    )


# ============================================================
# CLI / TEST
# ============================================================

def main():
    """Test on Marikh property."""
    print("جلب الإعلانات النشطة من arady.qa ...\n")

    all_villas = fetch_arady_listings('villas')
    print(f"إجمالي إعلانات الفلل: {len(all_villas)}")

    # Filter to similar to Marikh property: 490-736 m², villa
    filtered = filter_listings(
        all_villas,
        property_type='villa',
        min_area=490, max_area=736,
    )
    print(f"بعد فلتر المساحة 490-736م²: {len(filtered)}")

    # Show all matching
    print(f"\n{'─' * 90}")
    print(f"{'المنطقة':>15s} | {'مساحة':>5s} | {'سعر/م²':>8s} | {'سعر/قدم':>7s} | {'العمر':>5s} | {'الوزن':>5s} | الفئة")
    print(f"{'─' * 90}")
    for l in sorted(filtered, key=lambda x: x.get('age_days') if x.get('age_days') is not None else 999):
        loc = l.get('location', '?')
        area = l.get('area_m2', 0)
        pm2 = l.get('price_m2', 0)
        pft = l.get('price_ft', 0)
        age = l.get('age_days')
        age_str = f"{age:>4d}يوم" if age is not None else " ?يوم"
        w = l.get('weight', 0)
        tier = l.get('age_label', '?')
        print(f"{loc:>15s} | {area:>5.0f} | {pm2:>8,.0f} | {pft:>7,.0f} | {age_str} | {w:>5.2f} | {tier}")

    # Compute weighted median
    print(f"\n{'─' * 90}")
    result = weighted_listings_median(filtered)
    if result.get('n', 0) > 0:
        print(f"إجمالي الإعلانات: {result['n']}")
        print(f"العدد الفعلي (بعد الأوزان): {result['effective_n']}")
        print(f"الوسيط المرجّح: {result['weighted_median_m2']:,} ر.ق/م²"
              f" ({result['weighted_median_ft']:,} ر.ق/قدم)")
        print(f"خصم الإعلان: {result['discount_applied']*100:.0f}%")
        print(f"التقدير السوقي بعد الخصم: {result['estimated_market_m2']:,} ر.ق/م²"
              f" ({result['estimated_market_ft']:,} ر.ق/قدم)")
        print(f"النطاق: {result['min_price_m2']:,} - {result['max_price_m2']:,} ر.ق/م²")
        print(f"العمر: من {result['newest_days']} إلى {result['oldest_days']} يوم")
        print(f"التوزيع: {result['tier_breakdown']}")
    else:
        print("لا توجد إعلانات مطابقة")


if __name__ == '__main__':
    main()

"""
propertyfinder_client.py
========================

Stateless PropertyFinder Qatar client for the Cap Rate Calibration pipeline
(Sprint 2.19). Fetches rental search pages, parses the Next.js
``__NEXT_DATA__`` JSON blob, and yields normalized listing dicts.

Design constraints (Sprint 2.19 brief):
  - Pure stdlib only (urllib + json + re). No new requirements.txt deps.
  - Stateless: no module-level mutable cache; every call is self-contained.
  - RENTALS ONLY. This client never fetches sale listings — Rule E1 keeps
    listings out of the MoJ sale-comparison path entirely (see
    docs/Empirical_Findings.md §2).
  - GPS is preserved verbatim; district resolution is GIS's job, not ours
    (the calibrator cross-references against Vector/Districts). We never
    trust ``location.full_name``.

Derived from smoke_propertyfinder.py (committed 2026-05-20, ca046f1). The
``fetch`` helper here adds retry + exponential backoff for production use;
``extract_next_data`` is carried over unchanged.
"""

import json
import re
import time
import urllib.error
import urllib.request

# --------------------------------------------------------------------------
# Config
# --------------------------------------------------------------------------

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

# Verified-reachable rental search slugs (smoke test 2026-05-20, all HTTP 200).
# Keys are *categories*, not asset_types. Each listing is re-classified to an
# asset_type from its own ``property_type`` field — these URLs only bound the
# crawl, they do not define the asset_type.
RENT_CATEGORY_URLS = {
    "apartments": "https://www.propertyfinder.qa/en/rent/apartments-for-rent.html",
    "villas": "https://www.propertyfinder.qa/en/rent/villas-for-rent.html",
    "all": "https://www.propertyfinder.qa/en/rent/properties-for-rent.html",
}

# Qatar bounding box (lat 24.4-26.2, lon 50.7-51.7) — from smoke test §4.
QATAR_LAT_MIN, QATAR_LAT_MAX = 24.4, 26.2
QATAR_LON_MIN, QATAR_LON_MAX = 50.7, 51.7

# PropertyFinder property_type -> Thammen asset_type. Anything not mapped here
# is returned as asset_type=None and dropped by the calibrator (logged).
PROPERTY_TYPE_TO_ASSET = {
    "apartment": "apartment_building",
    "hotel apartments": "apartment_building",
    "penthouse": "apartment_building",
    "duplex": "apartment_building",
    "villa": "villa",
    "townhouse": "villa",
    "compound": "compound_small",
    "residential building": "tower",
    "whole building": "tower",
    "residential floor": "apartment_building",
}

# Period -> months multiplier to normalize any rent to a MONTHLY figure.
_PERIOD_TO_MONTHLY = {
    "monthly": 1.0,
    "yearly": 1.0 / 12.0,
    "weekly": 52.0 / 12.0,
    "daily": 365.0 / 12.0,
}


# --------------------------------------------------------------------------
# Low-level fetch + parse
# --------------------------------------------------------------------------

def fetch(url, timeout=20, retries=3, backoff_base=2.0):
    """Fetch ``url`` with retry + exponential backoff.

    Returns the raw response body as bytes, or raises the last exception if
    all attempts fail. 4xx (except 429) are not retried — they are permanent.
    """
    last_exc = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read()
        except urllib.error.HTTPError as e:
            last_exc = e
            # Permanent client errors: don't retry except rate-limit (429).
            if 400 <= e.code < 500 and e.code != 429:
                raise
        except Exception as e:  # noqa: BLE001 - network errors are diverse
            last_exc = e
        if attempt < retries - 1:
            time.sleep(backoff_base ** attempt)  # 1s, 2s, 4s ...
    raise last_exc


def extract_next_data(html):
    """Extract and parse the ``__NEXT_DATA__`` JSON blob.

    Accepts bytes or str. Returns the parsed dict, or None if the script tag
    is absent or the JSON is malformed (schema-change early-warning signal).
    Carried over unchanged from smoke_propertyfinder.py.
    """
    if isinstance(html, (bytes, bytearray)):
        try:
            html = html.decode("utf-8", errors="replace")
        except Exception:
            return None
    m = re.search(
        r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>',
        html, re.DOTALL,
    )
    if not m:
        return None
    try:
        return json.loads(m.group(1))
    except json.JSONDecodeError:
        return None


def _search_result(next_data):
    """Safely walk to props.pageProps.searchResult."""
    if not isinstance(next_data, dict):
        return {}
    return (
        next_data.get("props", {})
        .get("pageProps", {})
        .get("searchResult", {})
    ) or {}


# --------------------------------------------------------------------------
# Normalization
# --------------------------------------------------------------------------

def _to_float(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _to_int(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def map_property_type(property_type):
    """PropertyFinder property_type string -> Thammen asset_type (or None)."""
    if not property_type:
        return None
    return PROPERTY_TYPE_TO_ASSET.get(str(property_type).strip().lower())


def normalize_listing(listing):
    """Convert a raw PropertyFinder listing into a flat normalized dict.

    Returns None when the listing lacks the fields the calibrator needs
    (monthly rent, size, GPS inside Qatar). monthly_rent is always coerced to
    a per-MONTH figure regardless of the source period.
    """
    p = (listing or {}).get("property", {}) or {}
    price = p.get("price", {}) or {}
    size = p.get("size", {}) or {}
    loc = p.get("location", {}) or {}
    coords = loc.get("coordinates", {}) or {}

    rent_value = _to_float(price.get("value"))
    period = (price.get("period") or "").strip().lower()
    size_sqm = _to_float(size.get("value"))
    lat = _to_float(coords.get("lat"))
    lon = _to_float(coords.get("lon"))

    if rent_value is None or size_sqm is None or not size_sqm:
        return None
    if lat is None or lon is None:
        return None
    if not (QATAR_LAT_MIN <= lat <= QATAR_LAT_MAX and QATAR_LON_MIN <= lon <= QATAR_LON_MAX):
        return None  # GPS outside Qatar — reject (bad data / mislocated)

    mult = _PERIOD_TO_MONTHLY.get(period, 1.0)
    monthly_rent = rent_value * mult

    return {
        "id": p.get("id"),
        "property_type_raw": p.get("property_type"),
        "asset_type": map_property_type(p.get("property_type")),
        "monthly_rent": round(monthly_rent, 2),
        "rent_period_raw": period,
        "size_sqm": size_sqm,
        "rent_per_sqm": round(monthly_rent / size_sqm, 4),
        "lat": lat,
        "lon": lon,
        "bedrooms": _to_int(p.get("bedrooms")),
        "bathrooms": _to_int(p.get("bathrooms")),
        "furnished": (p.get("furnished") or "").strip().upper() or None,
        "completion_status": (p.get("completion_status") or "").strip() or None,
        "listed_date": p.get("listed_date"),
        "is_new_construction": bool(p.get("is_new_construction")),
        "pf_location": loc.get("full_name"),  # NOT authoritative — GIS decides
    }


# --------------------------------------------------------------------------
# High-level crawl
# --------------------------------------------------------------------------

def _build_page_url(base_url, page):
    if page <= 1:
        return base_url
    sep = "&" if "?" in base_url else "?"
    return f"{base_url}{sep}page={page}"


def fetch_listings_page(base_url, page=1, timeout=20, retries=3):
    """Fetch one page; return (normalized_listings, meta_dict).

    meta_dict carries total_count / page_count / page / per_page when present.
    On parse failure returns ([], {}) so callers can detect schema drift.
    """
    body = fetch(_build_page_url(base_url, page), timeout=timeout, retries=retries)
    nd = extract_next_data(body)
    if nd is None:
        return [], {}
    sr = _search_result(nd)
    raw = sr.get("listings", []) or []
    meta = sr.get("meta", {}) or {}
    out = []
    for L in raw:
        norm = normalize_listing(L)
        if norm is not None:
            out.append(norm)
    return out, meta


def fetch_rentals(category="apartments", target_n=200, max_pages=8,
                  delay_sec=2.0, timeout=20, retries=3):
    """Crawl a rental category until target_n listings or max_pages reached.

    ``category`` is one of RENT_CATEGORY_URLS keys. Returns a list of
    normalized rental dicts (RENTALS ONLY — this client has no sale path).
    Polite by default: delay_sec between page fetches.
    """
    base_url = RENT_CATEGORY_URLS.get(category)
    if base_url is None:
        raise ValueError(
            f"unknown rental category {category!r}; "
            f"valid: {sorted(RENT_CATEGORY_URLS)}"
        )
    collected = []
    for page in range(1, max_pages + 1):
        listings, meta = fetch_listings_page(base_url, page=page,
                                             timeout=timeout, retries=retries)
        collected.extend(listings)
        page_count = meta.get("page_count")
        if not listings:
            break  # empty page = end of results or schema drift
        if len(collected) >= target_n:
            break
        if page_count is not None and page >= page_count:
            break
        if page < max_pages:
            time.sleep(delay_sec)
    return collected[:target_n]

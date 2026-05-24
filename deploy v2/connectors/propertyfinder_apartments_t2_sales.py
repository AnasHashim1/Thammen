"""
propertyfinder_apartments_t2_sales.py — Sprint 2.21.3 — T2 connector (Lusail apartments-for-sale)

WHAT THIS CONNECTOR DOES
    Fetches Lusail apartment-for-sale listings from PropertyFinder Qatar
    as asking-tier (T2) evidence for the hybrid valuation framework
    (`hybrid_valuation.hybrid_valuation_v1()`, Sprint 2.21.2). Returns a
    list of normalized dicts with `value_per_m2` (RICS VPS 4 like-for-like,
    Rule E3 Constraint 7) for ingestion by the engine.

WHY ONLY PROPERTYFINDER (BRIEF §12 contingency)
    Sprint 2.21.3 Step 2 schema audit (2 rounds, Heroku v110→v113) found:
      - PF: SALES URL is `/en/buy/<city>/apartments-for-sale[-<area>].html`
        — Lusail-specific path returns 16 big_prices (>500K QAR), max 7.17M.
        Detail pages embed schema.org RealEstateListing in
        `<script id="plp-schema" type="application/ld+json">`.
      - arady: Next.js JS-hydrated listing content; sitemap.xml only
        exposes 5 category URLs (no individual listings). Deferred to a
        future Sprint 2.21.3.2 pending __NEXT_DATA__ probe.
    See 2p21p3_brief/connector_schema_audit.md for full evidence.

PUBLIC API (per BRIEF §3.2)
    get_apartment_sales_lusail(
        size_bracket: Optional[tuple[int, int]] = None,   # (min_m2, max_m2) filter
        use_cache: bool = True,
    ) -> list[dict]

OUTPUT SHAPE (per dict, per BRIEF §3.1)
    {
        "source":            "propertyfinder",
        "source_url":        "https://www.propertyfinder.qa/en/plp/buy/...",
        "tier":              "T2",
        "transaction_type":  "sale",
        "raw_price_qar":     2_500_000,        # int, BEFORE T2 discount
        "area_m2":           120.0,            # float
        "value_per_m2":      20833.0,          # float, raw_price / area
        "district":          "Lusail",
        "size_bracket":      "0-100" | "100-150" | "150-250" | "250+",
        "listing_date":      None,             # PF doesn't always expose this
        "raw_html_excerpt":  "<...max 500 chars...>",
    }

BEHAVIOR CONTRACT (BRIEF §3.2 + D-decisions)
    D5  rate-limit:    1 req/sec inter-fetch, max 3 list pages
    D6  network fail:  HTTPError/URLError → return [] (do NOT raise)
    D7  parse fail:    return [] for that listing, log to logger
    D8  AED skip:      listings with priceCurrency != "QAR" are skipped + warned
    D9  dedup:         intra-source by listing_id (last numeric before .html)
                       BEFORE counting; raw PF DOM duplicates ~6× (Pre-Sprint smoke)
    Rule E3 §7        output value_per_m2 in QAR/m² (no T2 discount applied here;
                       hybrid_valuation_v1 applies the discount per HYBRID_TIER_CONFIG)

CACHE
    24h TTL via t2_listings_cache.T2ListingsCache (D4). Key =
    (propertyfinder, Lusail, "<size_bracket_label>" or "all"). On cache miss
    fetch the network; on hit return instantly (<10ms).
"""

from __future__ import annotations
import json
import logging
import re
import time
import urllib.request
import urllib.error
from typing import Any, Optional

try:
    from t2_listings_cache import T2ListingsCache
except ImportError:                            # pragma: no cover
    T2ListingsCache = None  # type: ignore

logger = logging.getLogger("t2.propertyfinder")
# Module is library code; no handler attached. Embedding apps configure logging.

# ---------------------------------------------------------------------------
# Constants — single source of truth so tests can monkeypatch
# ---------------------------------------------------------------------------

LUSAIL_SALE_URL = (
    "https://www.propertyfinder.qa/en/buy/lusail/apartments-for-sale.html"
)
# Pagination scheme verified by Pre-Sprint smoke + PF general convention.
# PF supports ?page=N for N >= 2; page 1 is the bare URL.
PAGE_QUERY_PARAM = "page"
MAX_PAGES = 3                                  # D5
INTER_REQUEST_SLEEP_S = 1.0                    # D5
HTTP_TIMEOUT_S = 20
RAW_HTML_EXCERPT_CHARS = 500

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)

# /en/plp/buy/<slug>-<id>.html — id is the trailing numeric, our dedup key.
LISTING_PATH_RE = re.compile(r'/(?:en|ar)/plp/buy/[^\s"\'<>]+\.html')
LISTING_ID_RE = re.compile(r"-(\d+)\.html$")

# Detail-page JSON-LD schema block (verified in probe v2 raw HTML excerpt).
JSONLD_BLOCK_RE = re.compile(
    r'<script id="plp-schema"[^>]*?>\s*(\{.*?\})\s*</script>',
    re.DOTALL,
)

# Square-meter unit codes per UN/CEFACT (PF uses MTK; we accept MTQ + SQM too).
SQM_UNIT_CODES = frozenset({"MTK", "MTQ", "SQM", "M2"})


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _http_get(url: str) -> Optional[str]:
    """GET + return body text. None on HTTP/URL/timeout/decoding failure (D6).

    Logs at WARNING for non-200, INFO for transport errors. Never raises.
    """
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,ar;q=0.8",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT_S) as resp:
            if resp.status != 200:
                logger.warning("PF GET %s -> HTTP %d", url, resp.status)
                return None
            return resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        logger.warning("PF GET %s -> HTTPError %d", url, e.code)
        return None
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        logger.info("PF GET %s -> transport %s: %s", url, type(e).__name__, e)
        return None
    except Exception as e:                     # pragma: no cover
        logger.exception("PF GET %s -> unexpected %s", url, type(e).__name__)
        return None


def _page_url(page_num: int) -> str:
    """Page 1 = base URL; page >=2 adds ?page=N."""
    if page_num <= 1:
        return LUSAIL_SALE_URL
    return f"{LUSAIL_SALE_URL}?{PAGE_QUERY_PARAM}={page_num}"


def _extract_listing_urls(body: str) -> list[str]:
    """Find canonical /en/plp/buy/... URLs in a list-page body.

    Intra-source dedup per D9: PF DOM duplicates each link ~6×; we keep
    first occurrence by canonical path. Returns absolute URLs.
    """
    seen: set[str] = set()
    out: list[str] = []
    for path in LISTING_PATH_RE.findall(body):
        if path in seen:
            continue
        seen.add(path)
        out.append(f"https://www.propertyfinder.qa{path}")
    return out


def _listing_id(url: str) -> Optional[str]:
    """Return the trailing numeric id from /plp/buy/<slug>-<id>.html, or None."""
    m = LISTING_ID_RE.search(url)
    return m.group(1) if m else None


def _parse_jsonld(body: str) -> Optional[dict[str, Any]]:
    """Extract the schema.org RealEstateListing entity from detail HTML.

    Returns the inner `mainEntity.mainEntity` block (per probe v2 raw HTML
    structure), or the outer JSON itself if that path doesn't exist.
    None on missing/malformed block (D7).
    """
    m = JSONLD_BLOCK_RE.search(body)
    if not m:
        return None
    try:
        data = json.loads(m.group(1))
    except (ValueError, json.JSONDecodeError) as e:
        logger.info("PF jsonld parse error: %s", e)
        return None
    # PF nests RealEstateListing under mainEntity.mainEntity (probe-verified)
    entity = data
    for key in ("mainEntity", "mainEntity"):
        nxt = entity.get(key) if isinstance(entity, dict) else None
        if isinstance(nxt, dict):
            entity = nxt
    return entity if isinstance(entity, dict) else None


def _price_qar_from_entity(entity: dict[str, Any]) -> Optional[int]:
    """Return integer QAR price or None (D8 — skip AED + missing).

    Walks `entity.offers` which may be a dict or list of offers. Returns
    None if currency != QAR.
    """
    offers = entity.get("offers")
    if isinstance(offers, list):
        offers = offers[0] if offers else None
    if not isinstance(offers, dict):
        return None
    price = offers.get("price")
    currency = (offers.get("priceCurrency") or "").upper()
    if currency and currency != "QAR":
        logger.info("PF skip non-QAR listing (currency=%s)", currency)
        return None
    if price in (None, "", "0", 0):
        return None
    try:
        amt = int(float(price))
    except (TypeError, ValueError):
        return None
    if amt < 100_000 or amt > 1_000_000_000:
        # Sales-band sanity: a 50K QAR "price" on a sale listing is almost
        # certainly a rent or service fee; reject. 1B cap is just outlier guard.
        return None
    return amt


def _area_m2_from_entity(entity: dict[str, Any]) -> Optional[float]:
    """Return floor size in m², or None when missing/wrong-unit."""
    fs = entity.get("floorSize")
    if not isinstance(fs, dict):
        return None
    unit = (fs.get("unitCode") or "").upper().strip()
    if unit and unit not in SQM_UNIT_CODES:
        return None
    val = fs.get("value")
    try:
        m2 = float(val)
    except (TypeError, ValueError):
        return None
    if not (20.0 <= m2 <= 5_000.0):
        # Apartment sanity band; outside → wrong unit (sqft?) or bad data
        return None
    return m2


def _listing_date_from_entity(entity: dict[str, Any]) -> Optional[str]:
    """Best-effort listing-date extraction. PF doesn't always expose it."""
    for key in ("datePosted", "dateCreated", "uploadDate"):
        v = entity.get(key)
        if isinstance(v, str) and v.strip():
            return v[:10]                      # ISO date portion
    return None


def size_bracket_label(area_m2: float) -> str:
    """Map area to BRIEF §3.1 bracket label."""
    if area_m2 < 100:
        return "0-100"
    if area_m2 < 150:
        return "100-150"
    if area_m2 < 250:
        return "150-250"
    return "250+"


def _listing_is_lusail(body: str, entity: Optional[dict[str, Any]]) -> bool:
    """Sub-Lusail filter per BRIEF §3.2 closing note.

    PF's `l=63` (and `/en/buy/lusail/...`) returns Lusail + adjacent areas.
    Enforce strict Lusail-only by checking title/breadcrumb on each listing.
    """
    if entity:
        name = (entity.get("name") or "") if isinstance(entity, dict) else ""
        addr = entity.get("address") or {}
        if isinstance(addr, dict):
            for k in ("addressLocality", "addressRegion", "streetAddress"):
                v = addr.get(k)
                if isinstance(v, str) and re.search(r"lusail|لوسيل", v, re.IGNORECASE):
                    return True
        if re.search(r"lusail|لوسيل", name, re.IGNORECASE):
            return True
    return bool(re.search(r"\b[Ll]usail\b|لوسيل", body))


def _fetch_detail(url: str) -> Optional[dict[str, Any]]:
    """Fetch + parse one detail page. None on any failure (D6/D7)."""
    body = _http_get(url)
    if not body:
        return None
    entity = _parse_jsonld(body)
    if not entity:
        return None
    price = _price_qar_from_entity(entity)
    area = _area_m2_from_entity(entity)
    if price is None or area is None:
        return None
    if not _listing_is_lusail(body, entity):
        logger.info("PF skip non-Lusail listing %s", url)
        return None
    value_per_m2 = price / area
    return {
        "source":           "propertyfinder",
        "source_url":       url,
        "tier":             "T2",
        "transaction_type": "sale",
        "raw_price_qar":    price,
        "area_m2":          area,
        "value_per_m2":     round(value_per_m2, 2),
        "district":         "Lusail",
        "size_bracket":     size_bracket_label(area),
        "listing_date":     _listing_date_from_entity(entity),
        "raw_html_excerpt": body[:RAW_HTML_EXCERPT_CHARS],
    }


def _apply_size_bracket_filter(
    listings: list[dict[str, Any]],
    size_bracket: Optional[tuple[int, int]],
) -> list[dict[str, Any]]:
    if not size_bracket:
        return listings
    lo, hi = size_bracket
    return [r for r in listings if lo <= r["area_m2"] < hi]


def _cache_key_label(size_bracket: Optional[tuple[int, int]]) -> str:
    if not size_bracket:
        return "all"
    lo, hi = size_bracket
    return f"{int(lo)}-{int(hi)}"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_apartment_sales_lusail(
    size_bracket: Optional[tuple[int, int]] = None,
    use_cache: bool = True,
    cache: Optional[Any] = None,               # for test injection
) -> list[dict[str, Any]]:
    """Return Lusail apartment-for-sale listings as T2 evidence dicts.

    Network behaviour:
      - Hits the configured Lusail SALE URL across MAX_PAGES (D5).
      - INTER_REQUEST_SLEEP_S between requests (D5 rate-limit).
      - HTTPError / URLError / timeout / decode failures yield []
        (D6 — never raise).
      - JSON-LD parse failures skip that one listing + log (D7).
      - AED-priced listings are skipped + logged (D8).
      - Sub-Lusail filter on every listing (BRIEF §3.2 note).
      - Dedup by listing_id (D9) BEFORE counting.

    Cache: 24h TTL keyed by (propertyfinder, Lusail, <bracket-label>).
    Set `use_cache=False` to bypass for fresh fetches.
    """
    bracket_label = _cache_key_label(size_bracket)
    cache_obj = cache
    if cache_obj is None and use_cache and T2ListingsCache is not None:
        try:
            cache_obj = T2ListingsCache()
        except Exception as e:                 # pragma: no cover
            logger.info("T2 cache init failed: %s", e)
            cache_obj = None

    if cache_obj is not None and use_cache:
        hit = cache_obj.get("propertyfinder", "Lusail", bracket_label)
        if hit is not None:
            logger.info("PF cache hit (n=%d, bracket=%s)", len(hit), bracket_label)
            return hit

    # ── List-page fan-out (sequential per D5 polite-rate-limit) ──
    seen_ids: set[str] = set()
    detail_urls: list[str] = []
    for page in range(1, MAX_PAGES + 1):
        body = _http_get(_page_url(page))
        if not body:
            break                              # D6 — partial result OK
        urls_on_page = _extract_listing_urls(body)
        for url in urls_on_page:
            lid = _listing_id(url)
            if not lid or lid in seen_ids:
                continue
            seen_ids.add(lid)
            detail_urls.append(url)
        if page < MAX_PAGES:
            time.sleep(INTER_REQUEST_SLEEP_S)

    # ── Detail fetch (sequential per D5) ──
    listings: list[dict[str, Any]] = []
    for i, url in enumerate(detail_urls):
        row = _fetch_detail(url)
        if row is not None:
            listings.append(row)
        if i < len(detail_urls) - 1:
            time.sleep(INTER_REQUEST_SLEEP_S)

    listings = _apply_size_bracket_filter(listings, size_bracket)

    # Cache the full pre-filter result? No — filter is part of the cache
    # key (bracket_label). Each bracket-call caches its own filtered list.
    if cache_obj is not None and use_cache:
        cache_obj.set("propertyfinder", "Lusail", bracket_label, listings)

    logger.info(
        "PF returned %d Lusail apartments-for-sale (bracket=%s)",
        len(listings), bracket_label,
    )
    return listings


# ---------------------------------------------------------------------------
# CLI smoke (manual debugging — not used in production)
# ---------------------------------------------------------------------------

if __name__ == "__main__":                      # pragma: no cover
    import sys
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    result = get_apartment_sales_lusail(use_cache=False)
    print(f"\nTotal: {len(result)} Lusail apartment-for-sale listings")
    for row in result[:5]:
        print(json.dumps(
            {k: v for k, v in row.items() if k != "raw_html_excerpt"},
            ensure_ascii=False, indent=2,
        ))
    sys.exit(0 if result else 1)

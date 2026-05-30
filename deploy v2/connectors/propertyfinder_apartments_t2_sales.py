"""
propertyfinder_apartments_t2_sales.py — Sprint 2.21.3 — T2 connector (Lusail apartments-for-sale)

WHAT THIS CONNECTOR DOES
    Fetches Lusail apartment-for-sale listings from PropertyFinder Qatar
    as asking-tier (T2) evidence for the hybrid valuation framework
    (`hybrid_valuation.hybrid_valuation_v1()`, Sprint 2.21.2). Returns a
    list of normalized dicts with `value_per_m2` (RICS VPS 3 like-for-like,
    Rule E3 Constraint 7) for ingestion by the engine.

ARCHITECTURE — list-page JSON-LD only (Sprint 2.21.3 polish, post-deploy)
    PropertyFinder's `/en/buy/lusail/apartments-for-sale.html` ships ONE
    `<script type="application/ld+json">` ItemList containing 27 listings
    per page, each as a `WebPage.mainEntity.RealEstateListing` with:
        offers[0].priceSpecification.price       (int QAR)
        offers[0].priceSpecification.priceCurrency ("QAR" / "AED")
        floorSize.value + floorSize.unitText      (sqm)
        url                                       (canonical /plp/buy/...)
        address.addressLocality                   ("Lusail" / "The Pearl" / ...)
        address.addressRegion                     ("Marina District" / "Fox Hills" / ...)
    This is the single source of truth — no per-listing detail fetch.

WHY NOT DETAIL-PAGE FETCHES
    Initial implementation fetched each detail page individually to get the
    price + area. On Heroku post-deploy verification (v118) this took >30s
    (3 list pages + 24 detail fetches × 1.5s each) and tripped the router
    H12 timeout (HTTP 503). Audit-driven refactor (Rule #51 + Rule #52
    inverse: methodology-fix unmasked latency) replaced detail-fetch with
    list-page JSON-LD parse. New wall budget: ~5s for 3 list pages.

WHY ONLY PROPERTYFINDER (BRIEF §12 contingency)
    Sprint 2.21.3 Step 2 schema audit (Heroku v110→v113) found arady's
    listing content is JS-hydrated; its sitemap.xml only exposes 5 category
    URLs. Deferred to Sprint 2.21.3.2 candidate.

PUBLIC API (per BRIEF §3.2)
    get_apartment_sales_lusail(
        size_bracket: Optional[tuple[int, int]] = None,
        use_cache: bool = True,
        cache: Optional[Any] = None,   # for tests
    ) -> list[dict]

OUTPUT SHAPE (per dict)
    {
        "source":           "propertyfinder",
        "source_url":       "https://www.propertyfinder.qa/en/plp/buy/...",
        "tier":             "T2",
        "transaction_type": "sale",
        "raw_price_qar":    2_500_000,        # BEFORE T2 discount
        "area_m2":          120.0,
        "value_per_m2":     20833.33,         # raw_price / area
        "district":         "Lusail",
        "size_bracket":     "0-100" | "100-150" | "150-250" | "250+",
        "address_region":   "Marina District" | "Fox Hills" | ...,
        "listing_date":     None,             # PF list page doesn't expose
    }

BEHAVIOR CONTRACT (BRIEF §3.2 + D-decisions)
    D4  cache:         24h TTL, key=(propertyfinder, Lusail, <bracket-label>)
    D5  rate-limit:    1 req/sec inter-fetch, max 3 list pages
    D6  network fail:  HTTPError/URLError → return what we have (D6 partial)
    D7  parse fail:    skip that listing + log
    D8  AED skip:      listings with priceCurrency != "QAR" are skipped
    D9  dedup:         intra-source by listing url (rare on list page; PF
                       ItemList already dedups within a page)
    Rule E3 §7        output value_per_m2 in QAR/m² (no discount applied;
                       hybrid_valuation_v1 applies it per HYBRID_TIER_CONFIG)
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
    T2ListingsCache = None                     # type: ignore

logger = logging.getLogger("t2.propertyfinder")

# ---------------------------------------------------------------------------
# Configuration — module-level so tests can monkeypatch
# ---------------------------------------------------------------------------

LUSAIL_SALE_URL = (
    "https://www.propertyfinder.qa/en/buy/lusail/apartments-for-sale.html"
)
PAGE_QUERY_PARAM = "page"
MAX_PAGES = 3                                  # D5
INTER_REQUEST_SLEEP_S = 1.0                    # D5 polite rate-limit
HTTP_TIMEOUT_S = 20

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)

# Square-meter unit codes (PF uses "sqm" via unitText; we accept variants).
SQM_UNIT_VALUES = frozenset({"sqm", "sq m", "m²", "m2"})

# JSON-LD block — PF list pages emit it inline.
JSONLD_BLOCK_RE = re.compile(
    r'<script[^>]*type="application/ld\+json"[^>]*>\s*(.+?)\s*</script>',
    re.DOTALL,
)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _http_get(url: str) -> Optional[str]:
    """GET + return body text. None on any failure (D6). Never raises."""
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


def _walk_real_estate_listings(obj: Any) -> list[dict[str, Any]]:
    """Recursively collect every dict with @type containing RealEstateListing.

    PF's list-page JSON-LD wraps listings as
      ItemList → itemListElement[N] → WebPage.mainEntity.RealEstateListing.
    We walk depth-first because PF has tweaked the wrapping over time.
    """
    out: list[dict[str, Any]] = []
    if isinstance(obj, dict):
        t = obj.get("@type")
        if t == "RealEstateListing" or (isinstance(t, list) and "RealEstateListing" in t):
            out.append(obj)
        for v in obj.values():
            out.extend(_walk_real_estate_listings(v))
    elif isinstance(obj, list):
        for v in obj:
            out.extend(_walk_real_estate_listings(v))
    return out


def _extract_jsonld_listings(body: str) -> list[dict[str, Any]]:
    """Parse every ld+json block; return flat list of RealEstateListing entities."""
    out: list[dict[str, Any]] = []
    for raw in JSONLD_BLOCK_RE.findall(body):
        try:
            data = json.loads(raw)
        except (ValueError, json.JSONDecodeError) as e:
            logger.info("PF ld+json parse skip: %s", e)
            continue
        out.extend(_walk_real_estate_listings(data))
    return out


def _price_qar_from_entity(entity: dict[str, Any]) -> Optional[int]:
    """PF list page nests price under offers[0].priceSpecification.price.

    Returns None on AED, missing, or out-of-sales-band (D8 + sanity).
    """
    offers = entity.get("offers")
    if isinstance(offers, list):
        offers = offers[0] if offers else None
    if not isinstance(offers, dict):
        return None
    # PF list-page shape (preferred): offers[0].priceSpecification.price
    spec = offers.get("priceSpecification")
    if isinstance(spec, dict):
        price_raw = spec.get("price")
        currency = (spec.get("priceCurrency") or "").upper()
    else:
        # Fallback: detail-page shape uses offers.price directly
        price_raw = offers.get("price")
        currency = (offers.get("priceCurrency") or "").upper()
    if currency and currency != "QAR":
        logger.info("PF skip non-QAR (currency=%s)", currency)
        return None
    if price_raw in (None, "", 0, "0"):
        return None
    try:
        amt = int(float(price_raw))
    except (TypeError, ValueError):
        return None
    if amt < 100_000 or amt > 1_000_000_000:
        return None
    return amt


def _area_m2_from_entity(entity: dict[str, Any]) -> Optional[float]:
    """Return floor size in m²; PF uses floorSize.value (number) + unitText='sqm'."""
    fs = entity.get("floorSize")
    if not isinstance(fs, dict):
        return None
    unit = (fs.get("unitText") or fs.get("unitCode") or "").strip().lower()
    if unit and unit not in SQM_UNIT_VALUES:
        # Some entries use unitCode='MTK' (m²); accept that too
        if unit.upper() not in {"MTK", "MTQ"}:
            return None
    try:
        m2 = float(fs.get("value"))
    except (TypeError, ValueError):
        return None
    if not (20.0 <= m2 <= 5_000.0):
        return None
    return m2


def _listing_is_lusail(entity: dict[str, Any]) -> bool:
    """Sub-Lusail filter — PF '/en/buy/lusail/...' returns Lusail + adjacent."""
    addr = entity.get("address")
    if isinstance(addr, dict):
        loc = (addr.get("addressLocality") or "")
        reg = (addr.get("addressRegion") or "")
        if re.search(r"lusail|لوسيل|fox\s*hills|ghar\s*thuaileb", loc, re.IGNORECASE):
            return True
        if re.search(r"lusail|لوسيل|fox\s*hills|ghar\s*thuaileb", reg, re.IGNORECASE):
            return True
    name = entity.get("name") or ""
    if isinstance(name, str) and re.search(r"\blusail\b|لوسيل", name, re.IGNORECASE):
        return True
    return False


def size_bracket_label(area_m2: float) -> str:
    """Map area to BRIEF §3.1 bracket label."""
    if area_m2 < 100:
        return "0-100"
    if area_m2 < 150:
        return "100-150"
    if area_m2 < 250:
        return "150-250"
    return "250+"


def _entity_to_row(entity: dict[str, Any]) -> Optional[dict[str, Any]]:
    """Convert one RealEstateListing entity to the BRIEF §3.1 output shape.

    Returns None when any required field is missing/invalid (D7).
    """
    price = _price_qar_from_entity(entity)
    if price is None:
        return None
    area = _area_m2_from_entity(entity)
    if area is None:
        return None
    if not _listing_is_lusail(entity):
        logger.info("PF skip non-Lusail entity url=%s", entity.get("url"))
        return None
    url = entity.get("url") or entity.get("@id") or ""
    addr = entity.get("address") or {}
    region = (addr.get("addressRegion") if isinstance(addr, dict) else None) or ""
    vpm2 = price / area
    return {
        "source":           "propertyfinder",
        "source_url":       url,
        "tier":             "T2",
        "transaction_type": "sale",
        "raw_price_qar":    price,
        "area_m2":          area,
        "value_per_m2":     round(vpm2, 2),
        "district":         "Lusail",
        "size_bracket":     size_bracket_label(area),
        "address_region":   region,
        "listing_date":     None,
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
    cache: Optional[Any] = None,
) -> list[dict[str, Any]]:
    """Return Lusail apartment-for-sale listings as T2 evidence dicts.

    List-page-only extraction (Sprint 2.21.3 polish). For each page:
      1. Fetch the listing page (HTML).
      2. Parse the embedded JSON-LD ItemList.
      3. Walk for RealEstateListing entities.
      4. For each: extract price (QAR), area (m²), URL, region; skip AED;
         enforce sub-Lusail filter; compute value_per_m2.
      5. Dedup by URL across pages.
    Total wall budget for default (MAX_PAGES=3, INTER_REQUEST_SLEEP_S=1s):
    ~5s — well under Heroku 30s router timeout.

    Cache: 24h TTL keyed by (propertyfinder, Lusail, <bracket-label>).
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

    # ── List-page sweep (sequential per D5) ──
    listings: list[dict[str, Any]] = []
    seen_urls: set[str] = set()
    for page in range(1, MAX_PAGES + 1):
        body = _http_get(_page_url(page))
        if not body:
            break                              # D6 — partial result OK
        entities = _extract_jsonld_listings(body)
        page_added = 0
        for ent in entities:
            row = _entity_to_row(ent)
            if row is None:
                continue
            url = row["source_url"]
            if url in seen_urls:
                continue
            seen_urls.add(url)
            listings.append(row)
            page_added += 1
        logger.info("PF page %d: %d entities -> %d new rows", page, len(entities), page_added)
        if page < MAX_PAGES:
            time.sleep(INTER_REQUEST_SLEEP_S)

    listings = _apply_size_bracket_filter(listings, size_bracket)

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
        print(json.dumps(row, ensure_ascii=False, indent=2))
    sys.exit(0 if result else 1)

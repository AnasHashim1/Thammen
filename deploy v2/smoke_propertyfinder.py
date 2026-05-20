"""
smoke_propertyfinder.py
=======================

Pre-Sprint smoke test for PropertyFinder Qatar integration.
Run via: heroku run python smoke_propertyfinder.py

Purpose: verify from the Heroku production environment that:
  1. PropertyFinder is reachable (no Cloudflare challenge for Heroku IPs)
  2. Next.js __NEXT_DATA__ embedded JSON is parseable
  3. Slug-based URL patterns work for rent + sale + filtered searches
  4. Pagination works without JavaScript execution
  5. Rate-limit behavior is acceptable for a daily scheduler job

Self-contained: pure stdlib (urllib + json + re). No pip installs needed.

Rule followed: Custom Instructions §1 - External endpoint smoke test FIRST,
codified in Project Instructions §21.6 after 2026-05-19 Mthamen decision.
"""

import json
import re
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone

# ---- Config ----

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

# URL patterns we plan to use in the Cap Rate Calibration sprint
TEST_URLS = [
    ("rent_all", "https://www.propertyfinder.qa/en/rent/properties-for-rent.html"),
    ("rent_apt", "https://www.propertyfinder.qa/en/rent/apartments-for-rent.html"),
    ("rent_villa", "https://www.propertyfinder.qa/en/rent/villas-for-rent.html"),
    ("sale_all", "https://www.propertyfinder.qa/en/buy/properties-for-sale.html"),
    ("sale_villa", "https://www.propertyfinder.qa/en/buy/villas-for-sale.html"),
    ("sale_apt", "https://www.propertyfinder.qa/en/buy/apartments-for-sale.html"),
]

PAGINATION_URL = "https://www.propertyfinder.qa/en/rent/properties-for-rent.html?page=2"

RATE_TEST_URL = "https://www.propertyfinder.qa/en/rent/properties-for-rent.html"
RATE_TEST_COUNT = 5
RATE_TEST_DELAY_SEC = 2.0  # what a polite scheduler would use


# ---- Helpers ----

def fetch(url, timeout=20):
    """Fetch URL, return (status, body_bytes, elapsed_sec)."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    t0 = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read()
            return resp.status, body, time.monotonic() - t0
    except urllib.error.HTTPError as e:
        return e.code, b"", time.monotonic() - t0
    except Exception as e:
        return -1, str(e).encode(), time.monotonic() - t0


def extract_next_data(html_bytes):
    """Extract __NEXT_DATA__ JSON from a PropertyFinder HTML page."""
    try:
        html = html_bytes.decode("utf-8", errors="replace")
    except Exception:
        return None
    m = re.search(
        r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>',
        html, re.DOTALL
    )
    if not m:
        return None
    try:
        return json.loads(m.group(1))
    except json.JSONDecodeError:
        return None


def summarize_listing(listing):
    """Return one-line summary of a listing for verification."""
    p = listing.get("property", {})
    return {
        "id": p.get("id"),
        "type": p.get("property_type"),
        "price": p.get("price", {}).get("value"),
        "period": p.get("price", {}).get("period"),
        "size_sqm": p.get("size", {}).get("value"),
        "location": p.get("location", {}).get("full_name"),
        "gps": (
            p.get("location", {}).get("coordinates", {}).get("lat"),
            p.get("location", {}).get("coordinates", {}).get("lon"),
        ),
        "listed_date": p.get("listed_date"),
    }


# ---- Tests ----

def test_url_patterns():
    """Verify each URL pattern returns valid Next.js search result data."""
    print("=" * 60)
    print("TEST 1: URL patterns (slug-based)")
    print("=" * 60)
    results = {}
    for name, url in TEST_URLS:
        status, body, elapsed = fetch(url)
        nd = extract_next_data(body)
        if status != 200 or not nd:
            print(f"  ❌ {name:12s} HTTP={status} elapsed={elapsed:.2f}s next_data={'yes' if nd else 'NO'}")
            results[name] = {"ok": False, "status": status}
            continue
        sr = nd.get("props", {}).get("pageProps", {}).get("searchResult", {})
        listings = sr.get("listings", [])
        meta = sr.get("meta", {})
        if not listings:
            print(f"  ⚠️  {name:12s} HTTP=200 but 0 listings (schema may have changed)")
            results[name] = {"ok": False, "reason": "no_listings"}
            continue
        sample = summarize_listing(listings[0])
        print(f"  ✅ {name:12s} HTTP=200 total={meta.get('total_count'):>6} "
              f"pages={meta.get('page_count'):>5} sample={sample['type']}/{sample['price']} "
              f"QAR/{sample['size_sqm']}sqm elapsed={elapsed:.2f}s")
        results[name] = {
            "ok": True,
            "total_count": meta.get("total_count"),
            "page_count": meta.get("page_count"),
            "per_page": meta.get("per_page"),
            "sample": sample,
            "elapsed_sec": round(elapsed, 2),
        }
    return results


def test_pagination():
    """Verify ?page=2 returns different listings than page 1."""
    print()
    print("=" * 60)
    print("TEST 2: Pagination (no JS execution)")
    print("=" * 60)
    s1, b1, _ = fetch(TEST_URLS[0][1])
    s2, b2, _ = fetch(PAGINATION_URL)
    nd1 = extract_next_data(b1)
    nd2 = extract_next_data(b2)
    if not (nd1 and nd2):
        print("  ❌ Could not extract __NEXT_DATA__ on one or both pages")
        return False
    l1 = nd1["props"]["pageProps"]["searchResult"]["listings"]
    l2 = nd2["props"]["pageProps"]["searchResult"]["listings"]
    id1 = l1[0]["property"]["id"] if l1 else None
    id2 = l2[0]["property"]["id"] if l2 else None
    p1 = nd1["props"]["pageProps"]["searchResult"]["meta"]["page"]
    p2 = nd2["props"]["pageProps"]["searchResult"]["meta"]["page"]
    same_listings = id1 == id2
    ok = (p1 == 1 and p2 == 2 and not same_listings)
    icon = "✅" if ok else "❌"
    print(f"  {icon} Page1 meta.page={p1}, first_id={id1}")
    print(f"  {icon} Page2 meta.page={p2}, first_id={id2}")
    print(f"  {icon} Different listings: {not same_listings}")
    return ok


def test_rate_limiting():
    """Issue N requests with delay and verify all succeed."""
    print()
    print("=" * 60)
    print(f"TEST 3: Rate limit ({RATE_TEST_COUNT} requests, {RATE_TEST_DELAY_SEC}s apart)")
    print("=" * 60)
    statuses = []
    for i in range(RATE_TEST_COUNT):
        status, _, elapsed = fetch(RATE_TEST_URL)
        statuses.append(status)
        icon = "✅" if status == 200 else "❌"
        print(f"  {icon} Req {i+1}/{RATE_TEST_COUNT}: HTTP {status} elapsed={elapsed:.2f}s")
        if i < RATE_TEST_COUNT - 1:
            time.sleep(RATE_TEST_DELAY_SEC)
    all_ok = all(s == 200 for s in statuses)
    return all_ok


def test_listing_gps_quality():
    """Verify listings have GPS coordinates (needed for GIS cross-reference)."""
    print()
    print("=" * 60)
    print("TEST 4: GPS coordinate quality (needed for GIS cross-ref)")
    print("=" * 60)
    status, body, _ = fetch(TEST_URLS[0][1])
    nd = extract_next_data(body)
    if not nd:
        print("  ❌ Could not parse data")
        return False
    listings = nd["props"]["pageProps"]["searchResult"]["listings"][:10]
    with_gps = 0
    in_qatar_bounds = 0
    for L in listings:
        coords = L.get("property", {}).get("location", {}).get("coordinates", {})
        lat, lon = coords.get("lat"), coords.get("lon")
        if lat and lon:
            with_gps += 1
            # Qatar bbox: lat 24.4-26.2, lon 50.7-51.7
            if 24.4 <= lat <= 26.2 and 50.7 <= lon <= 51.7:
                in_qatar_bounds += 1
    print(f"  Listings sampled: {len(listings)}")
    print(f"  With GPS:         {with_gps}/{len(listings)}")
    print(f"  In Qatar bounds:  {in_qatar_bounds}/{len(listings)}")
    return with_gps >= 8 and in_qatar_bounds == with_gps


# ---- Main ----

def main():
    print()
    print("╔" + "═" * 58 + "╗")
    print("║  PropertyFinder Qatar Smoke Test                         ║")
    print("║  From: Heroku production environment                     ║")
    print(f"║  When: {datetime.now(timezone.utc).isoformat(timespec='seconds'):<50s}║")
    print("╚" + "═" * 58 + "╝")
    print()

    url_results = test_url_patterns()
    pagination_ok = test_pagination()
    rate_ok = test_rate_limiting()
    gps_ok = test_listing_gps_quality()

    print()
    print("=" * 60)
    print("VERDICT")
    print("=" * 60)
    all_urls_ok = all(r.get("ok") for r in url_results.values())
    overall = all_urls_ok and pagination_ok and rate_ok and gps_ok

    print(f"  URL patterns:  {'✅ all working' if all_urls_ok else '❌ some failed'}")
    print(f"  Pagination:    {'✅ works without JS' if pagination_ok else '❌ requires JS'}")
    print(f"  Rate limit:    {'✅ no throttling' if rate_ok else '❌ throttled'}")
    print(f"  GPS coverage:  {'✅ usable for GIS cross-ref' if gps_ok else '❌ insufficient'}")
    print()
    print(f"  OVERALL: {'✅ GREEN LIGHT for Sprint' if overall else '❌ DO NOT PROCEED'}")
    print()

    if overall:
        # Summary stats for Sprint planning
        rent_total = url_results.get("rent_all", {}).get("total_count", 0)
        sale_total = url_results.get("sale_all", {}).get("total_count", 0)
        avg_elapsed = sum(
            r.get("elapsed_sec", 0) for r in url_results.values() if r.get("ok")
        ) / max(1, sum(1 for r in url_results.values() if r.get("ok")))
        print(f"  Sprint planning inputs:")
        print(f"    Total rent listings:  {rent_total}")
        print(f"    Total sale listings:  {sale_total}")
        print(f"    Avg page latency:     {avg_elapsed:.2f}s")
        print(f"    Pages to scrape weekly: ~{(rent_total + sale_total) // 25}")
        print(f"    Estimated weekly time: ~{((rent_total + sale_total) // 25) * (avg_elapsed + RATE_TEST_DELAY_SEC) / 60:.1f} minutes")

    sys.exit(0 if overall else 1)


if __name__ == "__main__":
    main()

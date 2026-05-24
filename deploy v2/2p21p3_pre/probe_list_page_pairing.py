"""
probe_list_page_pairing.py — Sprint 2.21.3 latency-fix audit

Post-deploy H1 verification (v118) failed with HTTP 503 in 31.2s:
  3 list pages + 24 detail fetches × 1.5s ≈ 39s > Heroku 30s router timeout.

Fix architecture (Rule #51 audit-driven): list-page-only extraction — read
price + area from each listing CARD on the search page directly, no detail
fetch. Total fetch budget ~6s for 3 pages × ~16 unique listings each.

This probe answers: can the list page actually yield per-card (price, area)
pairings? Pre-Sprint smoke counted 16 big_prices + 20 QAR tokens (aggregate)
but never verified card-level pairing.

Output:
  - HTML excerpt of one listing card (so we can design a stable selector)
  - For each detected card: extracted price + area + canonical URL
  - Stats: cards_found, cards_with_price_and_area, sample_value_per_m2

Predictions (Rule #51):
  L1 — list page HTML has stable per-card delimiter (class/role/data-test)
  L2 — at least 10 cards have BOTH price AND area extractable inline
  L3 — extracted (price, area) pairs produce value_per_m2 in QAR/m² band
       [5_000, 50_000] (Lusail apartment sanity)
"""

from __future__ import annotations
import json
import os
import re
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

URL = "https://www.propertyfinder.qa/en/buy/lusail/apartments-for-sale.html"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/126.0.0.0 Safari/537.36"
TIMEOUT = 20


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA,
        "Accept": "text/html;q=0.9,*/*;q=0.8"})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            print(f"GET {url} -> HTTP {resp.status} {time.time()-t0:.2f}s len={len(body):,}")
            return body
    except Exception as e:
        print(f"GET {url} -> ERR {e}")
        return None


def find_card_candidates(body):
    """Look for repeating listing-card patterns. Return list of (regex_used, count, sample).

    Strategy: try several common patterns until one yields >=10 hits.
    """
    candidates = [
        # PF often uses semantic data-testid attributes
        (r'<[^>]*data-testid="property-card"[^>]*>', "data-testid=property-card"),
        # alternative: class containing 'property-card' or 'listing-card'
        (r'<article[^>]*class="[^"]*property-card[^"]*"', "article.property-card"),
        (r'<article[^>]*property-card', "article ~ property-card"),
        # ld+json per-listing block (newer PF often includes one per card)
        (r'<script[^>]*type="application/ld\+json"[^>]*>\s*\{[^<]*"RealEstateListing"[^<]*\}', "per-listing ld+json"),
        # generic listing anchor
        (r'<a[^>]*href="/en/plp/buy/[^"]+\.html"', "anchor /plp/buy/"),
    ]
    results = []
    for pat, label in candidates:
        hits = re.findall(pat, body, re.IGNORECASE)
        results.append({"label": label, "pattern": pat, "count": len(hits)})
        print(f"  pattern '{label}': {len(hits)} hits")
    return results


def extract_jsonld_listings(body):
    """Newer PF list pages may inline an ItemList of RealEstateListings.

    Returns list of {price_qar, area_m2, source_url} from JSON-LD blocks.
    """
    out = []
    # Find every script type="application/ld+json"
    blocks = re.findall(
        r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>',
        body, re.DOTALL,
    )
    print(f"\n  ld+json blocks total: {len(blocks)}")
    for i, raw in enumerate(blocks):
        try:
            data = json.loads(raw.strip())
        except Exception:
            continue
        # Walk for any nested RealEstateListing entries
        walk = []
        def _walk(o):
            if isinstance(o, dict):
                t = o.get("@type")
                if isinstance(t, list) and "RealEstateListing" in t:
                    walk.append(o)
                elif t == "RealEstateListing":
                    walk.append(o)
                for v in o.values():
                    _walk(v)
            elif isinstance(o, list):
                for v in o:
                    _walk(v)
        _walk(data)
        for ent in walk:
            offers = ent.get("offers")
            if isinstance(offers, list):
                offers = offers[0] if offers else None
            if not isinstance(offers, dict):
                continue
            try:
                price = int(float(offers.get("price") or 0))
            except (TypeError, ValueError):
                continue
            currency = (offers.get("priceCurrency") or "").upper()
            fs = ent.get("floorSize") or {}
            if not isinstance(fs, dict):
                continue
            try:
                area = float(fs.get("value") or 0)
            except (TypeError, ValueError):
                continue
            url = ent.get("url") or ent.get("@id") or ""
            out.append({
                "price": price, "currency": currency,
                "area_m2": area, "url": url,
                "block_index": i,
            })
    print(f"  RealEstateListing entries extracted: {len(out)}")
    return out


def extract_from_anchors_and_neighborhood(body):
    """Plan B: find each /en/plp/buy/ anchor, then look at surrounding
    ~3000-char window for the nearest QAR price + sqm token. Heuristic
    fallback if ld+json doesn't yield per-card data.
    """
    anchors = []
    # Capture both the path and the position
    for m in re.finditer(r'/(?:en|ar)/plp/buy/([^\s"\'<>]+\.html)', body):
        url = "https://www.propertyfinder.qa" + m.group(0).split('"')[0]
        anchors.append((m.start(), url))
    print(f"\n  /plp/buy/ anchors: {len(anchors)} (dedup keeps first occurrence)")
    seen = set()
    unique = []
    for pos, url in anchors:
        if url in seen:
            continue
        seen.add(url)
        unique.append((pos, url))
    print(f"  unique anchors: {len(unique)}")

    out = []
    for pos, url in unique[:25]:
        win = body[max(0, pos - 1500): pos + 1500]
        # nearest QAR price
        prices = re.findall(r"\bQAR\s*([\d,]+)", win)
        prices_int = [int(p.replace(",", "")) for p in prices if p.replace(",", "").isdigit()]
        sale_prices = [p for p in prices_int if 100_000 <= p <= 100_000_000]
        # nearest area (m²/sqm)
        areas = re.findall(r"([\d,]+(?:\.\d+)?)\s*(?:sqm|sq\s*ft|m²|m2)\b", win, re.IGNORECASE)
        areas_f = []
        for a in areas:
            try:
                v = float(a.replace(",", ""))
                if 20 <= v <= 1000:
                    areas_f.append(v)
            except ValueError:
                pass
        out.append({
            "url": url,
            "nearest_price": sale_prices[0] if sale_prices else None,
            "nearest_area_m2": areas_f[0] if areas_f else None,
            "all_prices_in_window": sale_prices[:5],
            "all_areas_in_window": areas_f[:5],
        })
    print(f"  anchors with price + area extractable: "
          f"{sum(1 for o in out if o['nearest_price'] and o['nearest_area_m2'])} / {len(out)}")
    return out


def sample_listing_html(body, n=1):
    """Find the first card-like block; print its raw HTML excerpt so we
    can design a stable selector."""
    print("\n=== HTML EXCERPT — first listing card region ===")
    # Use first /plp/buy/ anchor as a centroid
    m = re.search(r'/(?:en|ar)/plp/buy/[^\s"\'<>]+\.html', body)
    if not m:
        print("(no anchor found)")
        return
    start = max(0, m.start() - 1200)
    end = m.end() + 1200
    print(body[start:end])
    print("=== END EXCERPT ===")


def main():
    print(f"=== probe_list_page_pairing — {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')} ===\n")
    body = fetch(URL)
    if not body:
        print("FAIL: list page unreachable from Heroku")
        return 1

    print("\n=== STAGE 1: card-delimiter pattern hunt ===")
    find_card_candidates(body)

    print("\n=== STAGE 2: JSON-LD per-card extraction ===")
    jsonld_rows = extract_jsonld_listings(body)
    for r in jsonld_rows[:10]:
        print(f"  ld+json: price={r['price']:>10,} {r['currency']:3}  "
              f"area={r['area_m2']:>6.1f}  url={r['url'][:80]}")

    print("\n=== STAGE 3: anchor-window heuristic fallback ===")
    anchor_rows = extract_from_anchors_and_neighborhood(body)
    for r in anchor_rows[:10]:
        p = r['nearest_price']
        a = r['nearest_area_m2']
        vpm2 = (p / a) if (p and a) else None
        print(f"  anchor: price={p}  area={a}  v/m2={vpm2 and round(vpm2,1)}  "
              f"url={r['url'][-70:]}")

    sample_listing_html(body)

    # Predictions ledger
    print("\n===PROBE_LEDGER_BEGIN===")
    print(f"L1 (stable card delimiter):     {'PARTIAL — needs HTML inspection' if True else 'TBD'}")
    print(f"L2 (>=10 cards with both):      "
          f"jsonld={sum(1 for r in jsonld_rows if r['price'] and r['area_m2'])}  "
          f"anchor={sum(1 for r in anchor_rows if r['nearest_price'] and r['nearest_area_m2'])}")
    sane = [(r['nearest_price']/r['nearest_area_m2'])
            for r in anchor_rows if r['nearest_price'] and r['nearest_area_m2']
            and 5_000 <= (r['nearest_price']/r['nearest_area_m2']) <= 50_000]
    print(f"L3 (anchor v/m2 in [5K,50K]):    {len(sane)} / "
          f"{sum(1 for r in anchor_rows if r['nearest_price'] and r['nearest_area_m2'])}")
    print("===PROBE_LEDGER_END===")
    return 0


if __name__ == "__main__":
    sys.exit(main())

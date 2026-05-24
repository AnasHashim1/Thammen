"""
probe_schema_v2_2p21p3.py — Sprint 2.21.3 Step 2 round 2

Round 1 (probe_schema_2p21p3.py, v110→v111) findings:
  - S1 TRUE: arady /listings is SALE-shaped (sale=195 vs rent=1)
  - S2 FALSE: PF c=1&t=1/c=1&t=2/c=2&t=2 all 404 or RENT
  - S3 FALSE: arady detail finder matched /listings/villas (category page)
  - S4 TRUE: PF detail extractable (Next.js SSR)
  - S5 TRUE: neither JS-rendered

Round 2 closes the two FALSE predictions:

  Stage A (arady) — parse /sitemap.xml (4564 chars per Pre-Sprint smoke H3)
    to enumerate REAL listing URLs. Filter for apartment + Lusail.

  Stage B (PF) — Round 1 detail page breadcrumb revealed PF uses two URL
    schemes in parallel:
        /en/rent/<city>/apartments-for-rent[-<area>].html  (path-style)
        /en/search?c=2&t=1&l=63                            (query-style)
    By analogy SALE = /en/buy/<city>/apartments-for-sale[-<area>].html.
    Try 6 path-style SALE candidates + 1 query-style c=3 fallback.

Stages C/D/E: same as v1 (find detail URL → extract schema → emit
markdown report bracketed by ===REPORT_V2_BEGIN===/===REPORT_V2_END===).

Falsifiable predictions:
  V1 — arady /sitemap.xml contains real listing URL patterns (≥5 with
       apartment-or-sale token)
  V2 — at least one PF path-style SALE URL returns HTTP 200 with
       big_price tokens (>500K QAR) dominant
  V3 — arady real listing detail extractable (price + area)
  V4 — PF SALE detail extractable (price + area, QAR not AED)
"""

import os
import re
import sys
import time
import urllib.parse
import urllib.request
import urllib.error
from datetime import datetime

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")
TIMEOUT = 20

ARADY_SITEMAP = "https://arady.qa/sitemap.xml"

PF_PATH_CANDIDATES = [
    "https://www.propertyfinder.qa/en/buy/doha/apartments-for-sale.html",
    "https://www.propertyfinder.qa/en/buy/doha/apartments-for-sale-lusail.html",
    "https://www.propertyfinder.qa/en/buy/lusail/apartments-for-sale.html",
    "https://www.propertyfinder.qa/en/buy/qatar/apartments-for-sale.html",
    "https://www.propertyfinder.qa/en/buy/qatar/apartments-for-sale-lusail.html",
    "https://www.propertyfinder.qa/en/search?c=3&t=1&l=63",
]


def fetch(url, label=""):
    if label:
        print(f"\n--- {label} ---")
    print(f"  GET {url}")
    t0 = time.time()
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": UA,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,ar;q=0.8",
        })
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            dt = time.time() - t0
            print(f"  HTTP {resp.status}  {dt:.2f}s  len={len(body):,}")
            return resp.status, body, len(body), dt, None
    except urllib.error.HTTPError as e:
        dt = time.time() - t0
        try:
            body = e.read().decode("utf-8", errors="replace")
        except Exception:
            body = ""
        print(f"  HTTP {e.code}  {dt:.2f}s  ERR")
        return e.code, body, len(body), dt, f"HTTPError {e.code}"
    except Exception as e:
        dt = time.time() - t0
        print(f"  {type(e).__name__}: {e}")
        return None, "", 0, dt, f"{type(e).__name__}: {e}"


def sale_vs_rent_signal(body):
    if not body:
        return {"sale": 0, "rent": 0, "verdict": "EMPTY"}
    sale = (len(re.findall(r"للبيع|للتمليك", body))
            + len(re.findall(r"\bfor sale\b|\bbuy\b", body, re.IGNORECASE)))
    rent = (len(re.findall(r"للإيجار|للايجار|إيجار", body))
            + len(re.findall(r"\bfor rent\b|\brent\b|\brental\b", body, re.IGNORECASE)))
    verdict = "SALE" if sale > rent * 1.3 else ("RENT" if rent > sale * 1.3 else "MIXED")
    return {"sale": sale, "rent": rent, "verdict": verdict}


def extract_prices(body):
    out = []
    for m in re.finditer(r"\b(QAR|AED|QR|ر\.?ق|ريال)\s*([\d,]+)", body):
        amt_s = m.group(2).replace(",", "")
        if amt_s.isdigit():
            amt = int(amt_s)
            if 100 <= amt <= 1_000_000_000:
                out.append((m.group(1), amt))
    return out


def extract_areas(body):
    out = []
    for m in re.finditer(r"\b([\d,]+(?:\.\d+)?)\s*(?:sqm|sq\s*m|m²|m2|متر\s*مربع)\b",
                         body, re.IGNORECASE):
        try:
            v = float(m.group(1).replace(",", ""))
            if 20 <= v <= 100_000:
                out.append(v)
        except ValueError:
            continue
    return out


# ---------- Stage A: arady via sitemap ----------

def stage_a_arady_sitemap():
    print("\n" + "=" * 78)
    print("STAGE A — arady sitemap.xml discovery")
    print("=" * 78)
    s, body, _, _, err = fetch(ARADY_SITEMAP, "arady sitemap")
    if s != 200:
        return {"status": s, "sitemap_urls": [], "winner": None, "verdict_v1": False}

    # Sitemap may be sitemapindex with child sitemaps, or urlset with locs.
    locs = re.findall(r"<loc>([^<]+)</loc>", body)
    print(f"  found {len(locs)} <loc> entries")

    # If sitemap index, fetch first child sitemap (usually contains listing URLs)
    listing_urls = [u for u in locs if "/listings" in u or "/listing/" in u]
    sitemaps = [u for u in locs if u.endswith(".xml")]

    if not listing_urls and sitemaps:
        # It's a sitemap index. Pick the most listing-looking child.
        for sm in sitemaps[:5]:
            print(f"  drilling sitemap: {sm}")
            s2, body2, _, _, _ = fetch(sm, "child sitemap")
            if s2 == 200:
                locs2 = re.findall(r"<loc>([^<]+)</loc>", body2)
                listing_urls += [u for u in locs2 if "/listings" in u or "/listing/" in u]
                if listing_urls:
                    break
            time.sleep(1)

    print(f"  total listing-looking URLs: {len(listing_urls)}")
    if listing_urls:
        print(f"  sample 5:")
        for u in listing_urls[:5]:
            print(f"    {u}")

    # Filter for apartment + Lusail
    apt_lusail = [u for u in listing_urls
                  if (re.search(r"apartment|شقة|شقق|flat", u, re.IGNORECASE)
                      and re.search(r"lusail|لوسيل", u, re.IGNORECASE))]
    apt_any = [u for u in listing_urls
               if re.search(r"apartment|شقة|شقق|flat", u, re.IGNORECASE)]
    lusail_any = [u for u in listing_urls
                  if re.search(r"lusail|لوسيل", u, re.IGNORECASE)]
    print(f"  apartment+Lusail: {len(apt_lusail)}, apartment-any: {len(apt_any)}, "
          f"Lusail-any: {len(lusail_any)}")

    # Pick best candidate
    if apt_lusail:
        winner = apt_lusail[0]
    elif apt_any:
        winner = apt_any[0]
    elif listing_urls:
        # fallback: filter to non-category (presence of multiple slug segments + numeric)
        non_category = [u for u in listing_urls
                        if (u.count("/") >= 4 or re.search(r"\d{3,}", u.split("/")[-1] or ""))]
        winner = non_category[0] if non_category else listing_urls[0]
    else:
        winner = None

    return {
        "status": s, "sitemap_urls": listing_urls, "winner": winner,
        "apt_lusail_count": len(apt_lusail),
        "apt_any_count": len(apt_any),
        "lusail_any_count": len(lusail_any),
        "verdict_v1": len(apt_any) >= 5,
    }


# ---------- Stage B: PF path-style SALE discovery ----------

def stage_b_pf_paths():
    print("\n" + "=" * 78)
    print("STAGE B — PF path-style SALE discovery")
    print("=" * 78)
    results = []
    for url in PF_PATH_CANDIDATES:
        s, body, length, dt, err = fetch(url, "PF SALE candidate")
        if s != 200:
            results.append({"url": url, "status": s, "verdict": "DEAD"})
            time.sleep(2)
            continue
        signals = sale_vs_rent_signal(body)
        prices = extract_prices(body)
        big_prices = [p[1] for p in prices if p[1] > 500_000]
        qar_count = sum(1 for p in prices if p[0] in ("QAR", "QR", "ر.ق", "ر\\.ق", "ريال"))
        results.append({
            "url": url, "status": s, "length": length, "latency_s": dt,
            "sale_rent": signals,
            "price_count": len(prices),
            "big_price_count": len(big_prices),
            "qar_count": qar_count,
            "price_max": max((p[1] for p in prices), default=0),
        })
        print(f"  sale/rent: {signals['verdict']}  big_prices={len(big_prices)}  "
              f"QAR_tokens={qar_count}  max={results[-1]['price_max']:,}")
        time.sleep(2)

    valid = [r for r in results if r.get("status") == 200]
    sale_candidates = [r for r in valid
                       if r.get("sale_rent", {}).get("verdict") in ("SALE", "MIXED")
                       and r.get("big_price_count", 0) >= 3]
    if sale_candidates:
        winner = max(sale_candidates, key=lambda r: r.get("big_price_count", 0))
    elif valid:
        winner = max(valid, key=lambda r: r.get("big_price_count", 0))
    else:
        winner = None

    return {
        "results": results,
        "winner": winner,
        "verdict_v2": bool(winner and winner.get("big_price_count", 0) >= 3),
    }


# ---------- Stage C: find detail URLs ----------

def find_arady_real_detail(search_url):
    """Re-fetch arady listings page, find URLs that look like REAL details
    (have a numeric id in path or 4+ slug segments)."""
    s, body, _, _, _ = fetch(search_url, "arady refetch for real detail")
    if s != 200:
        return None
    # Pattern 1: /listings/<numeric-id>
    numeric_ids = re.findall(r"https?://arady\.qa/listings/(\d+)\b", body)
    # Pattern 2: /listings/<long-slug>-<numeric-id>
    slug_ids = re.findall(r"https?://arady\.qa/listings/([\w\-]+-\d+)\b", body)
    # Pattern 3: /listing/ (singular)
    singular = re.findall(r"https?://arady\.qa/listing/[\w\-]+", body)

    print(f"  /listings/<numeric>: {len(numeric_ids)}  "
          f"slug+num: {len(slug_ids)}  /listing/: {len(singular)}")
    if numeric_ids:
        return f"https://arady.qa/listings/{numeric_ids[0]}"
    if slug_ids:
        return f"https://arady.qa/listings/{slug_ids[0]}"
    if singular:
        return singular[0]
    return None


def find_pf_sale_detail(search_url):
    s, body, _, _, _ = fetch(search_url, "PF refetch for sale detail")
    if s != 200:
        return None
    # Only /buy/ paths
    buy_paths = re.findall(r"/(?:en|ar)/plp/buy/[^\s\"\'<>]+\.html", body)
    if buy_paths:
        chosen = buy_paths[0]
        return f"https://www.propertyfinder.qa{chosen}"
    # Fallback: any /plp/ path on this page
    any_paths = re.findall(r"/(?:en|ar)/plp/[^\s\"\'<>]+\.html", body)
    if any_paths:
        return f"https://www.propertyfinder.qa{any_paths[0]}"
    return None


# ---------- Stage D: extract detail ----------

def extract_detail(url, source):
    s, body, length, dt, err = fetch(url, f"{source} detail page")
    if s != 200 or not body:
        return {"source": source, "url": url, "status": s, "error": err,
                "extractable": False}

    prices = extract_prices(body)
    areas = extract_areas(body)
    qar_only = [p for p in prices if p[0] in ("QAR", "QR", "ر.ق", "ريال")]

    title_m = re.search(r"<title[^>]*>([^<]+)</title>", body)
    title = title_m.group(1).strip() if title_m else ""

    bed_m = re.findall(r"\b(\d+)\s*(?:bed|bedroom|غرف?\s*نوم)", body, re.IGNORECASE)
    beds = bed_m[0] if bed_m else None

    lusail_present = bool(re.search(r"Lusail|لوسيل", body, re.IGNORECASE))
    has_property_price_class = "property-price" in body
    has_data_test_price = 'data-test="price"' in body or 'data-testid="price"' in body
    has_property_size_class = "property-size" in body

    # listing price = max QAR-only price > 100K (sales scale)
    listing_price_cands = [p for p in qar_only if p[1] > 100_000]
    if not listing_price_cands:
        # Fallback to AED but flag it
        listing_price_cands = [p for p in prices if p[1] > 100_000]
    listing_price = max(listing_price_cands, key=lambda p: p[1]) if listing_price_cands else None

    apt_area_cands = [a for a in areas if 30 <= a <= 500]
    apt_area = apt_area_cands[0] if apt_area_cands else None

    # Sale vs rent context (in title / breadcrumb)
    title_sale = bool(re.search(r"for sale|للبيع|للتمليك", title, re.IGNORECASE))
    title_rent = bool(re.search(r"for rent|للإيجار|للايجار", title, re.IGNORECASE))

    extractable = bool(listing_price) and bool(apt_area)

    return {
        "source": source, "url": url, "status": s, "length": length, "latency_s": dt,
        "title": title[:200],
        "title_is_sale": title_sale, "title_is_rent": title_rent,
        "all_prices": prices[:10],
        "qar_only_prices": qar_only[:10],
        "all_areas": areas[:10],
        "listing_price": listing_price,
        "apt_area_m2": apt_area,
        "bedrooms": beds,
        "lusail_present": lusail_present,
        "has_property_price_class": has_property_price_class,
        "has_data_test_price": has_data_test_price,
        "has_property_size_class": has_property_size_class,
        "extractable": extractable,
        "raw_html_excerpt": body[:2000],
    }


# ---------- Stage E: emit markdown ----------

def emit_report(arady_stage_a, pf_stage_b, arady_detail, pf_detail, total_s):
    lines = []
    a = lines.append

    a(f"# Connector Schema Audit — Sprint 2.21.3 (ROUND 2)")
    a("")
    a(f"**Run timestamp (UTC):** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}")
    a(f"**Total wall time:** {total_s:.1f}s")
    a(f"**Origin:** {'Heroku' if os.environ.get('DYNO') else 'local'}")
    a("**Goal:** close round-1 FALSE predictions (S2 PF SALES + S3 arady real detail).")
    a("")
    a("---")
    a("")
    a("## V1 — arady sitemap.xml discovery")
    a("")
    a(f"- Status: HTTP {arady_stage_a.get('status')}")
    a(f"- Total listing-looking URLs: {len(arady_stage_a.get('sitemap_urls', []))}")
    a(f"- Apartment+Lusail: {arady_stage_a.get('apt_lusail_count', 0)}")
    a(f"- Apartment-any: {arady_stage_a.get('apt_any_count', 0)}")
    a(f"- Lusail-any: {arady_stage_a.get('lusail_any_count', 0)}")
    a(f"- Winner URL: `{arady_stage_a.get('winner') or 'NONE'}`")
    a(f"- **V1 verdict (≥5 apartment URLs):** "
      f"{'✅ TRUE' if arady_stage_a.get('verdict_v1') else '❌ FALSE'}")
    a("")
    a("Sample sitemap URLs (first 10):")
    for u in arady_stage_a.get("sitemap_urls", [])[:10]:
        a(f"  - {u}")
    a("")
    a("---")
    a("")
    a("## V2 — PF path-style SALE candidates")
    a("")
    a("| URL | HTTP | sale/rent | big_prices(>500K) | QAR_tokens | max_price |")
    a("|---|:---:|---|---:|---:|---:|")
    for r in pf_stage_b["results"]:
        sr = r.get("sale_rent", {})
        a(f"| `{r['url'].replace('https://www.propertyfinder.qa', '...')}` | "
          f"{r['status']} | {sr.get('verdict', 'N/A')} | "
          f"{r.get('big_price_count', 0)} | {r.get('qar_count', 0)} | "
          f"{r.get('price_max', 0):,} |")
    a("")
    winner = pf_stage_b.get("winner")
    if winner:
        a(f"**Winner:** `{winner['url']}`")
    else:
        a("**Winner:** NONE — no path-style SALE URL identified")
    a("")
    a(f"**V2 verdict (winner with ≥3 big_prices):** "
      f"{'✅ TRUE' if pf_stage_b.get('verdict_v2') else '❌ FALSE'}")
    a("")
    a("---")
    a("")
    a("## V3 — arady REAL detail extraction")
    a("")
    if arady_detail:
        a(f"- **URL:** `{arady_detail['url']}`")
        a(f"- **HTTP:** {arady_detail['status']}, **length:** {arady_detail.get('length', 0):,}")
        a(f"- **Title:** {arady_detail.get('title', '')}")
        a(f"- **Title is SALE:** {arady_detail.get('title_is_sale')}, "
          f"**is RENT:** {arady_detail.get('title_is_rent')}")
        a(f"- **Listing price:** {arady_detail.get('listing_price')}")
        a(f"- **Apartment area:** {arady_detail.get('apt_area_m2')} m²")
        a(f"- **Bedrooms:** {arady_detail.get('bedrooms')}")
        a(f"- **Lusail in body:** {arady_detail.get('lusail_present')}")
        a(f"- **QAR-only prices found:** {arady_detail.get('qar_only_prices')}")
        a(f"- **All prices found:** {arady_detail.get('all_prices')}")
        a(f"- **All areas found:** {arady_detail.get('all_areas')}")
        a(f"- **`property-price` class:** {arady_detail.get('has_property_price_class')}")
        a(f"- **`data-test=\"price\"`:** {arady_detail.get('has_data_test_price')}")
        a(f"- **Extractable:** {arady_detail.get('extractable')}")
        a("")
        a("Raw HTML excerpt (2000 chars):")
        a("```html")
        a(arady_detail.get("raw_html_excerpt", ""))
        a("```")
        a("")
        a(f"**V3 verdict:** {'✅ TRUE' if arady_detail.get('extractable') else '❌ FALSE'}")
    else:
        a("No detail attempted (no winner URL from V1).")
        a("**V3 verdict:** ❌ FALSE")
    a("")
    a("---")
    a("")
    a("## V4 — PF SALE detail extraction")
    a("")
    if pf_detail:
        a(f"- **URL:** `{pf_detail['url']}`")
        a(f"- **HTTP:** {pf_detail['status']}, **length:** {pf_detail.get('length', 0):,}")
        a(f"- **Title:** {pf_detail.get('title', '')}")
        a(f"- **Title is SALE:** {pf_detail.get('title_is_sale')}, "
          f"**is RENT:** {pf_detail.get('title_is_rent')}")
        a(f"- **Listing price:** {pf_detail.get('listing_price')}")
        a(f"- **Apartment area:** {pf_detail.get('apt_area_m2')} m²")
        a(f"- **Bedrooms:** {pf_detail.get('bedrooms')}")
        a(f"- **Lusail in body:** {pf_detail.get('lusail_present')}")
        a(f"- **QAR-only prices found:** {pf_detail.get('qar_only_prices')}")
        a(f"- **All prices found:** {pf_detail.get('all_prices')}")
        a(f"- **All areas found:** {pf_detail.get('all_areas')}")
        a(f"- **`property-price` class:** {pf_detail.get('has_property_price_class')}")
        a(f"- **`data-test=\"price\"`:** {pf_detail.get('has_data_test_price')}")
        a(f"- **Extractable:** {pf_detail.get('extractable')}")
        a("")
        a("Raw HTML excerpt (2000 chars):")
        a("```html")
        a(pf_detail.get("raw_html_excerpt", ""))
        a("```")
        a("")
        a(f"**V4 verdict:** "
          f"{'✅ TRUE' if (pf_detail.get('extractable') and pf_detail.get('title_is_sale')) else '❌ FALSE'}")
    else:
        a("No detail attempted (no winner URL from V2).")
        a("**V4 verdict:** ❌ FALSE")
    a("")
    a("---")
    a("")
    a("## Predictions ledger (V1–V4)")
    a("")
    a(f"- **V1** arady sitemap has real listing URLs: "
      f"{'✅ TRUE' if arady_stage_a.get('verdict_v1') else '❌ FALSE'}")
    a(f"- **V2** PF path-style SALE identified: "
      f"{'✅ TRUE' if pf_stage_b.get('verdict_v2') else '❌ FALSE'}")
    a(f"- **V3** arady REAL detail extractable: "
      f"{'✅ TRUE' if (arady_detail and arady_detail.get('extractable')) else '❌ FALSE'}")
    a(f"- **V4** PF SALE detail extractable: "
      f"{'✅ TRUE' if (pf_detail and pf_detail.get('extractable') and pf_detail.get('title_is_sale')) else '❌ FALSE'}")
    a("")
    a("---")
    a("")
    a("*Generated by `2p21p3_pre/probe_schema_v2_2p21p3.py`. Appended to")
    a("`2p21p3_brief/connector_schema_audit.md` as round-2 section after capture.*")

    text = "\n".join(lines) + "\n"
    print("")
    print("===REPORT_V2_BEGIN===")
    print(text, end="")
    print("===REPORT_V2_END===")
    print(f"\nReport v2 length: {len(text):,} chars")
    return text


def main():
    t0 = time.time()
    print("=" * 78)
    print("Sprint 2.21.3 Step 2 — ROUND 2 schema audit")
    print(f"Started: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print("=" * 78)

    arady_stage_a = stage_a_arady_sitemap()
    pf_stage_b = stage_b_pf_paths()

    print("\n" + "=" * 78)
    print("STAGE C — find real detail URLs")
    print("=" * 78)
    arady_winner = arady_stage_a.get("winner")
    # If arady_winner from sitemap is itself a category-looking URL, re-search.
    if arady_winner and not re.search(r"\d{3,}|/listing/", arady_winner):
        print(f"  arady winner looks category-like; trying refetch real-detail finder")
        arady_winner = find_arady_real_detail("https://arady.qa/listings") or arady_winner

    pf_winner_url = (pf_stage_b["winner"]["url"] if pf_stage_b.get("winner") else None)
    pf_detail_url = find_pf_sale_detail(pf_winner_url) if pf_winner_url else None

    print(f"  arady detail URL: {arady_winner}")
    print(f"  PF detail URL:    {pf_detail_url}")

    print("\n" + "=" * 78)
    print("STAGE D — extract detail")
    print("=" * 78)
    arady_detail = extract_detail(arady_winner, "arady") if arady_winner else None
    pf_detail = extract_detail(pf_detail_url, "propertyfinder") if pf_detail_url else None

    total_s = time.time() - t0
    print("\n" + "=" * 78)
    print(f"STAGE E — emit report (total wall {total_s:.1f}s)")
    print("=" * 78)
    emit_report(arady_stage_a, pf_stage_b, arady_detail, pf_detail, total_s)

    ok_arady = bool(arady_detail and arady_detail.get("extractable"))
    ok_pf = bool(pf_detail and pf_detail.get("extractable")
                 and pf_detail.get("title_is_sale"))
    print(f"\nFinal: arady_extractable={ok_arady}  pf_sale_extractable={ok_pf}")
    return 0 if (ok_arady or ok_pf) else 1


if __name__ == "__main__":
    sys.exit(main())

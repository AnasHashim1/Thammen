"""
probe_schema_2p21p3.py — Sprint 2.21.3 Step 2 — Detail-page schema audit

Goal per BRIEF_2p21p3 §9 step 2:
    "Pre-implementation audit (small): fetch one Lusail apartment listing
    from each source, document actual detail-page schema in
    2p21p3_brief/connector_schema_audit.md. Stop and report if schema
    differs materially from smoke expectations."

Pre-Sprint 2.21.3 smoke confirmed RENT URLs (c=2&t=1 for PF, /listings
for arady). Sprint 2.21.3 is SALES — so the probe must FIRST discover the
sales URL pattern, THEN fetch one apartment-for-sale detail per source.

Stages:
  A. arady SALES URL discovery
       try: /listings (default), /buy, /listings?type=sale,
            /listings/sale, /apartments-for-sale
       success = HTTP 200 + body contains "للبيع" / "for sale" / "بيع"
                 markers more than "للإيجار" / "rent" / "إيجار"
  B. PropertyFinder SALES URL discovery
       try category combos: c=1&t=1, c=1&t=2, c=2&t=1, c=2&t=2
       success = HTTP 200 + price tokens in millions (sales) > thousands (rent)
  C. From best SALES URL on each source: extract first Lusail apartment
     listing detail URL
  D. Fetch that detail page; extract:
       price (QAR), area (m²), location string, bedrooms, listing date,
       primary price selector, primary area selector
  E. Print 2p21p3_brief/connector_schema_audit.md content to stdout
     bracketed by ===REPORT_BEGIN===/===REPORT_END=== markers
     (Heroku slug filesystem is ephemeral; capture via heroku run logs).

Falsifiable predictions (Rule #51):
  S1 — arady sales URL pattern identified (HTTP 200 + sale markers > rent markers)
  S2 — PF sales c/t combination identified (HTTP 200 + median price > 500K QAR)
  S3 — arady detail page exposes BOTH price (QAR) AND area (m²) extractable
  S4 — PF detail page exposes BOTH price (QAR) AND area (m²) extractable
  S5 — neither source is JavaScript-rendered (BRIEF §12 open question)

If S5 FALSE on arady: report shrinks Sprint to PF-only (BRIEF §12).
If S5 FALSE on PF: report stops here (no fallback source, Sprint blocked).

Read-only. Stdlib only. Writes ONE local file (markdown report).
Designed for `heroku run python 2p21p3_pre/probe_schema_2p21p3.py`
but also runnable locally (limited by IP geo).

Usage:
    heroku run python 2p21p3_pre/probe_schema_2p21p3.py
"""

import json
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

REPORT_PATH = "2p21p3_brief/connector_schema_audit.md"

# Stage A — arady sales URL candidates
ARADY_CANDIDATES = [
    "https://arady.qa/listings",
    "https://arady.qa/listings?type=sale",
    "https://arady.qa/listings/sale",
    "https://arady.qa/buy",
    "https://arady.qa/sale",
    "https://arady.qa/apartments-for-sale",
]

# Stage B — PropertyFinder c/t combinations (l=63 = Lusail per Pre-Sprint smoke)
# PF convention typically c=1 = sale, c=2 = rent; t=1 = apartment, t=2 = villa
PF_CANDIDATES = [
    ("c=1&t=1", "https://www.propertyfinder.qa/en/search?c=1&t=1&l=63"),
    ("c=2&t=1", "https://www.propertyfinder.qa/en/search?c=2&t=1&l=63"),  # RENT baseline
    ("c=1&t=2", "https://www.propertyfinder.qa/en/search?c=1&t=2&l=63"),
]


def fetch(url, label=""):
    """Return (status, body, length, latency_s, error)."""
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


def js_rendered_signals(body):
    """Heuristic detection of JS-rendered SPA pages.
    Returns dict with risk markers."""
    if not body:
        return {"empty": True}
    body_lower = body.lower()
    return {
        "react_root_marker":     "id=\"root\"" in body or "id=\"__next\"" in body,
        "vue_app_marker":        "id=\"app\"" in body and "<script" in body_lower,
        "noscript_warning":      "<noscript" in body_lower and "javascript" in body_lower,
        "spa_loading_text":      "loading..." in body_lower or "please wait" in body_lower,
        "low_static_content":    len(re.findall(r"<p[^>]*>[^<]{20,}</p>", body)) < 3,
        "high_script_ratio":     len(re.findall(r"<script", body, re.IGNORECASE)) > 30,
        "scripts_count":         len(re.findall(r"<script", body, re.IGNORECASE)),
    }


def sale_vs_rent_signal(body):
    """Count sale vs rent markers in body."""
    if not body:
        return {"sale": 0, "rent": 0, "verdict": "EMPTY"}
    sale_ar = len(re.findall(r"للبيع|بيع|للتمليك", body))
    sale_en = len(re.findall(r"\bfor sale\b|\bbuy\b", body, re.IGNORECASE))
    rent_ar = len(re.findall(r"للإيجار|للايجار|إيجار|ايجار", body))
    rent_en = len(re.findall(r"\bfor rent\b|\brental\b|\brent\b", body, re.IGNORECASE))
    sale = sale_ar + sale_en
    rent = rent_ar + rent_en
    verdict = "SALE" if sale > rent * 1.3 else ("RENT" if rent > sale * 1.3 else "MIXED")
    return {"sale": sale, "rent": rent, "verdict": verdict,
            "sale_ar": sale_ar, "sale_en": sale_en,
            "rent_ar": rent_ar, "rent_en": rent_en}


def extract_prices(body):
    """Return list of (currency, amount_int) tokens found in body."""
    prices = []
    for m in re.finditer(r"\b(QAR|AED|QR|ر\.?ق|ريال)\s*([\d,]+)", body):
        currency = m.group(1)
        amount = int(m.group(2).replace(",", "")) if m.group(2).replace(",", "").isdigit() else 0
        if 100 <= amount <= 1_000_000_000:  # plausible range
            prices.append((currency, amount))
    return prices


def extract_areas(body):
    """Return list of area values in m² found in body."""
    areas = []
    for m in re.finditer(r"\b([\d,]+(?:\.\d+)?)\s*(?:sqm|sq\s*m|m²|m2|متر\s*مربع)\b",
                         body, re.IGNORECASE):
        try:
            v = float(m.group(1).replace(",", ""))
            if 20 <= v <= 100_000:  # plausible apartment+plot range
                areas.append(v)
        except ValueError:
            continue
    return areas


# --- Stage A: arady SALES URL discovery ---

def probe_arady_sales():
    print("\n" + "=" * 78)
    print("STAGE A — arady SALES URL discovery")
    print("=" * 78)

    results = []
    for url in ARADY_CANDIDATES:
        s, body, length, dt, err = fetch(url, "arady candidate")
        if s != 200:
            results.append({"url": url, "status": s, "verdict": "DEAD", "error": err})
            time.sleep(1)
            continue
        signals = sale_vs_rent_signal(body)
        js = js_rendered_signals(body)
        prices = extract_prices(body)
        results.append({
            "url": url, "status": s, "length": length, "latency_s": dt,
            "sale_rent": signals, "js": js,
            "price_count": len(prices),
            "price_max": max((p[1] for p in prices), default=0),
            "price_min": min((p[1] for p in prices), default=0),
        })
        print(f"  sale/rent: {signals['verdict']}  "
              f"(sale={signals['sale']} rent={signals['rent']})  "
              f"prices_found={len(prices)} max={results[-1]['price_max']:,}")
        time.sleep(2)

    # Winner = highest sale-verdict url
    sale_urls = [r for r in results if r.get("sale_rent", {}).get("verdict") == "SALE"]
    if sale_urls:
        winner = max(sale_urls, key=lambda r: r["sale_rent"]["sale"])
    else:
        # Fallback: best MIXED (likely /listings shows both)
        mixed_urls = [r for r in results if r.get("sale_rent", {}).get("verdict") == "MIXED"]
        winner = max(mixed_urls, key=lambda r: r["sale_rent"]["sale"]) if mixed_urls else None

    return results, winner


# --- Stage B: PropertyFinder SALES URL discovery ---

def probe_pf_sales():
    print("\n" + "=" * 78)
    print("STAGE B — PropertyFinder SALES c/t discovery")
    print("=" * 78)

    results = []
    for combo, url in PF_CANDIDATES:
        s, body, length, dt, err = fetch(url, f"PF {combo}")
        if s != 200:
            results.append({"combo": combo, "url": url, "status": s,
                            "verdict": "DEAD", "error": err})
            time.sleep(2)
            continue
        signals = sale_vs_rent_signal(body)
        js = js_rendered_signals(body)
        prices = extract_prices(body)
        # SALE filter: median price token > 500K (rent typically 5K-50K)
        big_prices = [p[1] for p in prices if p[1] > 500_000]
        results.append({
            "combo": combo, "url": url, "status": s, "length": length, "latency_s": dt,
            "sale_rent": signals, "js": js,
            "price_count": len(prices),
            "big_price_count": len(big_prices),
            "price_max": max((p[1] for p in prices), default=0),
        })
        print(f"  sale/rent: {signals['verdict']}  "
              f"big_prices(>500K)={len(big_prices)}  "
              f"max_price={results[-1]['price_max']:,}")
        time.sleep(2)

    # Winner = combo with most big_prices (sale heuristic)
    valid = [r for r in results if r.get("status") == 200]
    if not valid:
        return results, None
    # Prefer combo where big_prices dominate AND sale_verdict != RENT
    sale_candidates = [r for r in valid if r.get("big_price_count", 0) > 0
                       and r.get("sale_rent", {}).get("verdict") != "RENT"]
    if sale_candidates:
        winner = max(sale_candidates, key=lambda r: r["big_price_count"])
    else:
        winner = max(valid, key=lambda r: r.get("big_price_count", 0))

    return results, winner


# --- Stage C: find first Lusail apartment detail URL on each source ---

def find_arady_detail(search_url):
    """Re-fetch arady search URL, find first listing detail URL with Lusail context."""
    s, body, _, _, _ = fetch(search_url, "arady re-fetch for detail extraction")
    if s != 200:
        return None
    # arady listing URL patterns: /listings/<slug>, /properties/<slug>
    candidates = re.findall(r"https?://arady\.qa/(?:listings|properties)/[\w\-]+", body)
    candidates += [
        f"https://arady.qa{m}" if not m.startswith("http") else m
        for m in re.findall(r'(?:href|src)=["\'](/(?:listings|properties)/[\w\-]+)', body)
    ]
    seen = set()
    unique = []
    for c in candidates:
        if c not in seen:
            seen.add(c)
            unique.append(c)
    print(f"  arady detail candidates: {len(unique)} unique")
    return unique[0] if unique else None


def find_pf_detail(search_url):
    """Re-fetch PF search URL, find first Lusail apartment plp URL."""
    s, body, _, _, _ = fetch(search_url, "PF re-fetch for detail extraction")
    if s != 200:
        return None
    paths = re.findall(r"/(?:en|ar)/plp/[^\s\"\'<>]+\.html", body)
    seen = set()
    unique = []
    for p in paths:
        if p not in seen:
            seen.add(p)
            unique.append(p)
    print(f"  PF detail candidates: {len(unique)} unique")
    if not unique:
        return None
    # Prefer ones with "lusail" in slug if present
    lusail_paths = [p for p in unique if "lusail" in p.lower()]
    chosen = lusail_paths[0] if lusail_paths else unique[0]
    return f"https://www.propertyfinder.qa{chosen}"


# --- Stage D: detail extraction ---

def extract_detail(url, source):
    """Fetch detail page, extract schema fields. Returns dict."""
    s, body, length, dt, err = fetch(url, f"{source} detail page")
    if s != 200 or not body:
        return {"source": source, "url": url, "status": s, "error": err,
                "extractable": False}

    prices = extract_prices(body)
    areas = extract_areas(body)
    js = js_rendered_signals(body)

    # Title heuristics
    title_m = re.search(r"<title[^>]*>([^<]+)</title>", body)
    title = title_m.group(1).strip() if title_m else ""

    # Bedroom count
    bed_matches = re.findall(r"\b(\d+)\s*(?:bed|bedroom|غرف?\s*نوم)", body, re.IGNORECASE)
    beds = bed_matches[0] if bed_matches else None

    # Location heuristics
    lusail_present = bool(re.search(r"Lusail|لوسيل", body, re.IGNORECASE))

    # CSS marker checks
    has_property_price_class = "property-price" in body
    has_data_test_price = 'data-test="price"' in body or 'data-testid="price"' in body
    has_property_size_class = "property-size" in body

    # Price most likely to be the listing price = max amount > 100K
    listing_price_candidates = [p for p in prices if p[1] > 100_000]
    listing_price = max(listing_price_candidates, key=lambda p: p[1]) if listing_price_candidates else None

    # Area most likely to be apartment area = first area in 30-500 m² range
    apt_area_candidates = [a for a in areas if 30 <= a <= 500]
    apt_area = apt_area_candidates[0] if apt_area_candidates else None

    extractable = bool(listing_price) and bool(apt_area)

    return {
        "source": source, "url": url, "status": s, "length": length, "latency_s": dt,
        "title": title[:200],
        "all_prices": prices[:10],
        "all_areas": areas[:10],
        "listing_price": listing_price,
        "apt_area_m2": apt_area,
        "bedrooms": beds,
        "lusail_present": lusail_present,
        "has_property_price_class": has_property_price_class,
        "has_data_test_price": has_data_test_price,
        "has_property_size_class": has_property_size_class,
        "js_signals": js,
        "extractable": extractable,
        "raw_html_excerpt": body[:2000],
    }


# --- Stage E: write markdown report ---

def write_report(arady_results, arady_winner, pf_results, pf_winner,
                 arady_detail, pf_detail, total_seconds):
    lines = []
    a = lines.append
    a(f"# Connector Schema Audit — Sprint 2.21.3")
    a("")
    a(f"**Run timestamp (UTC):** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}")
    a(f"**Total wall time:** {total_seconds:.1f}s")
    a(f"**Origin:** {'Heroku' if os.environ.get('DYNO') else 'local sandbox'}")
    a("**Goal:** Confirm detail-page schema for one Lusail apartment listing per source.")
    a("**Source brief:** BRIEF_2p21p3 §9 step 2 + §12 (JS-rendering risk for arady).")
    a("")
    a("---")
    a("")
    a("## 1. Falsifiable predictions")
    a("")
    a("| # | Prediction | Result | Evidence |")
    a("|---|---|:---:|---|")

    # S1
    s1 = ("✅ TRUE" if arady_winner and arady_winner.get("sale_rent", {}).get("verdict") == "SALE"
          else ("⚠️ PARTIAL" if arady_winner and arady_winner.get("sale_rent", {}).get("verdict") == "MIXED"
                else "❌ FALSE"))
    s1_evidence = (f"winner: {arady_winner['url']}, verdict: {arady_winner['sale_rent']['verdict']}"
                   if arady_winner else "no working candidate")
    a(f"| **S1** | arady sales URL pattern identified | {s1} | {s1_evidence} |")

    # S2
    s2 = ("✅ TRUE" if pf_winner and pf_winner.get("big_price_count", 0) >= 3
          else "❌ FALSE")
    s2_evidence = (f"combo: {pf_winner['combo']}, big_prices(>500K)={pf_winner.get('big_price_count', 0)}, "
                   f"max={pf_winner.get('price_max', 0):,}"
                   if pf_winner else "no SALE-shaped combo found")
    a(f"| **S2** | PF sales c/t combination identified | {s2} | {s2_evidence} |")

    # S3
    s3 = "✅ TRUE" if arady_detail and arady_detail.get("extractable") else "❌ FALSE"
    s3_evidence = (
        f"price={arady_detail.get('listing_price')}, area={arady_detail.get('apt_area_m2')}m²"
        if arady_detail and arady_detail.get("extractable")
        else (f"price={arady_detail.get('listing_price') if arady_detail else 'N/A'}, "
              f"area={arady_detail.get('apt_area_m2') if arady_detail else 'N/A'}"))
    a(f"| **S3** | arady detail exposes price + area extractable | {s3} | {s3_evidence} |")

    # S4
    s4 = "✅ TRUE" if pf_detail and pf_detail.get("extractable") else "❌ FALSE"
    s4_evidence = (
        f"price={pf_detail.get('listing_price')}, area={pf_detail.get('apt_area_m2')}m²"
        if pf_detail and pf_detail.get("extractable")
        else f"detail probe failed or non-extractable")
    a(f"| **S4** | PF detail exposes price + area extractable | {s4} | {s4_evidence} |")

    # S5 — JS rendering check
    def is_likely_js(detail):
        if not detail:
            return None
        js = detail.get("js_signals", {})
        return (js.get("react_root_marker") or js.get("vue_app_marker")) and js.get("low_static_content")
    arady_js = is_likely_js(arady_detail)
    pf_js = is_likely_js(pf_detail)
    s5 = ("✅ TRUE" if arady_js is False and pf_js is False
          else (f"⚠️ MIXED — arady_js={arady_js} pf_js={pf_js}"))
    a(f"| **S5** | Neither source JS-rendered | {s5} | arady JS-risk={arady_js}, PF JS-risk={pf_js} |")

    a("")
    a("---")
    a("")
    a("## 2. arady — URL discovery + detail")
    a("")
    a("### 2.1 Candidate scan")
    a("")
    a("| URL | HTTP | sale/rent | big_prices |")
    a("|---|:---:|---|---:|")
    for r in arady_results:
        sr = r.get("sale_rent", {})
        a(f"| `{r['url']}` | {r['status']} | {sr.get('verdict', 'N/A')} "
          f"(s={sr.get('sale', 0)} r={sr.get('rent', 0)}) | {r.get('price_count', 0)} |")
    a("")
    if arady_winner:
        a(f"**Winner:** `{arady_winner['url']}` — verdict {arady_winner['sale_rent']['verdict']}")
    else:
        a("**Winner:** none — no candidate cleared sale/rent threshold.")
    a("")
    a("### 2.2 Detail page extracted")
    a("")
    if arady_detail:
        a(f"- **URL:** `{arady_detail['url']}`")
        a(f"- **HTTP:** {arady_detail['status']}, **length:** {arady_detail.get('length', 0):,}")
        a(f"- **Title:** {arady_detail.get('title', '')}")
        a(f"- **Listing price:** {arady_detail.get('listing_price')} (apt range >100K)")
        a(f"- **Apartment area:** {arady_detail.get('apt_area_m2')} m² (30-500 m² range)")
        a(f"- **Bedrooms:** {arady_detail.get('bedrooms')}")
        a(f"- **Lusail markers in body:** {arady_detail.get('lusail_present')}")
        a(f"- **All prices found (first 10):** {arady_detail.get('all_prices')}")
        a(f"- **All areas found (first 10):** {arady_detail.get('all_areas')}")
        a("")
        a(f"**CSS / data-attr markers:**")
        a(f"- `property-price` class: {arady_detail.get('has_property_price_class')}")
        a(f"- `data-test=\"price\"`: {arady_detail.get('has_data_test_price')}")
        a(f"- `property-size` class: {arady_detail.get('has_property_size_class')}")
        a("")
        a(f"**JS-rendering signals:** {arady_detail.get('js_signals')}")
        a("")
        a("**Raw HTML excerpt (first 2000 chars):**")
        a("```html")
        a(arady_detail.get("raw_html_excerpt", ""))
        a("```")
    else:
        a("No detail extracted (search winner unavailable or no listing URL discovered).")
    a("")
    a("---")
    a("")
    a("## 3. PropertyFinder — URL discovery + detail")
    a("")
    a("### 3.1 Candidate scan")
    a("")
    a("| Combo | HTTP | sale/rent | big_prices(>500K) | max_price |")
    a("|---|:---:|---|---:|---:|")
    for r in pf_results:
        sr = r.get("sale_rent", {})
        a(f"| `{r['combo']}` | {r['status']} | {sr.get('verdict', 'N/A')} | "
          f"{r.get('big_price_count', 0)} | {r.get('price_max', 0):,} |")
    a("")
    if pf_winner:
        a(f"**Winner combo:** `{pf_winner['combo']}` — `{pf_winner['url']}`")
    else:
        a("**Winner:** none — no combo identified as SALE.")
    a("")
    a("### 3.2 Detail page extracted")
    a("")
    if pf_detail:
        a(f"- **URL:** `{pf_detail['url']}`")
        a(f"- **HTTP:** {pf_detail['status']}, **length:** {pf_detail.get('length', 0):,}")
        a(f"- **Title:** {pf_detail.get('title', '')}")
        a(f"- **Listing price:** {pf_detail.get('listing_price')}")
        a(f"- **Apartment area:** {pf_detail.get('apt_area_m2')} m²")
        a(f"- **Bedrooms:** {pf_detail.get('bedrooms')}")
        a(f"- **Lusail markers in body:** {pf_detail.get('lusail_present')}")
        a(f"- **All prices found (first 10):** {pf_detail.get('all_prices')}")
        a(f"- **All areas found (first 10):** {pf_detail.get('all_areas')}")
        a("")
        a(f"**CSS / data-attr markers:**")
        a(f"- `property-price` class: {pf_detail.get('has_property_price_class')}")
        a(f"- `data-test=\"price\"`: {pf_detail.get('has_data_test_price')}")
        a(f"- `property-size` class: {pf_detail.get('has_property_size_class')}")
        a("")
        a(f"**JS-rendering signals:** {pf_detail.get('js_signals')}")
        a("")
        a("**Raw HTML excerpt (first 2000 chars):**")
        a("```html")
        a(pf_detail.get("raw_html_excerpt", ""))
        a("```")
    else:
        a("No detail extracted.")
    a("")
    a("---")
    a("")
    a("## 4. Recommendations for connector build (Sprint 2.21.3 Step 3)")
    a("")
    a("(Filled at build time based on which predictions came back TRUE.)")
    a("")
    a("- If S1 + S3 TRUE → arady connector builds against the winning search URL")
    a("- If S2 + S4 TRUE → PF connector builds against the winning c/t combo")
    a("- If S5 FALSE on arady → shrink Sprint to PF-only per BRIEF §12 contingency")
    a("- If S5 FALSE on PF → Sprint blocked; pause and reassess (no fallback)")
    a("")
    a("---")
    a("")
    a("*Generated by `2p21p3_pre/probe_schema_2p21p3.py`. Cleanup pattern: same as")
    a("Pre-Sprint smoke v108→v109 (push probe, run, push cleanup without probe).*")

    text = "\n".join(lines) + "\n"
    # stdout-only mode (Heroku slug filesystem is ephemeral; capture from logs).
    # Markers below let `heroku run` output be extracted locally to
    # 2p21p3_brief/connector_schema_audit.md.
    print("")
    print("===REPORT_BEGIN===")
    print(text, end="")
    print("===REPORT_END===")
    print(f"\nReport length: {len(text):,} chars  (captured via stdout markers)")
    return text


def main():
    t0 = time.time()
    print("=" * 78)
    print("Sprint 2.21.3 Step 2 — Detail-page schema audit")
    print(f"Started: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print("=" * 78)

    arady_results, arady_winner = probe_arady_sales()
    pf_results, pf_winner = probe_pf_sales()

    print("\n" + "=" * 78)
    print("STAGE C — find detail URLs")
    print("=" * 78)
    arady_detail_url = find_arady_detail(arady_winner["url"]) if arady_winner else None
    pf_detail_url = find_pf_detail(pf_winner["url"]) if pf_winner else None
    print(f"  arady detail URL: {arady_detail_url}")
    print(f"  PF detail URL:    {pf_detail_url}")

    print("\n" + "=" * 78)
    print("STAGE D — extract detail")
    print("=" * 78)
    arady_detail = extract_detail(arady_detail_url, "arady") if arady_detail_url else None
    pf_detail = extract_detail(pf_detail_url, "propertyfinder") if pf_detail_url else None

    total_s = time.time() - t0
    print("\n" + "=" * 78)
    print(f"STAGE E — write report (total wall {total_s:.1f}s)")
    print("=" * 78)
    write_report(arady_results, arady_winner, pf_results, pf_winner,
                 arady_detail, pf_detail, total_s)

    # Exit code: 0 if at least one source extractable, 1 otherwise
    ok = bool((arady_detail and arady_detail.get("extractable")) or
              (pf_detail and pf_detail.get("extractable")))
    print(f"\nFinal: {'AT LEAST ONE SOURCE EXTRACTABLE' if ok else 'BOTH SOURCES UNEXTRACTABLE'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

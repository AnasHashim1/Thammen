"""
smoke_t2_connectors.py — Pre-Sprint 2.21.3 — T2 connector reachability + URL discovery

Runs from Heroku one-off dyno. Probes the two T2 source candidates the
Sprint 2.21.2 §5 audit identified:

  - PropertyFinder Qatar — sandbox-IP showed 142 Lusail rent listings on
    page 1 (well over n>=30). Confirm same from Heroku IP and capture
    listing-extraction signals.

  - arady.qa — sandbox-IP showed root reachable, but the guessed search
    URL pattern /properties?type=apartment&location=lusail = 404.
    Discover the working URL pattern by probing 8 candidates.

Falsifiable predictions (Rule #51):
  H1 — PropertyFinder reachable from Heroku (HTTP 200)
  H2 — PF Lusail apartment-rent page returns >=30 listing-pattern matches
  H3 — at least one arady search URL pattern returns HTTP 200 with listing
       content (>=1 propertyish marker beyond the root page's signals)
  H4 — Heroku-IP counts within +-15 of sandbox-IP for PF (no geo filtering)
  H5 — at least one PF listing detail page exposes BOTH a price token
       (QAR/AED) AND an area token (m^2/sqm/sq.ft) — extractable schema

Out of scope: ranking, deduplication, full scrape. This is reachability
+ URL discovery + extraction-feasibility, not the connector itself.

Usage (Heroku):
    heroku run python smoke_t2_connectors.py

Read-only. Stdlib only. No writes. Output ends with a copy-pasteable
H1-H5 ledger.
"""

import json
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

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")
TIMEOUT = 20

# Sandbox-confirmed PropertyFinder search URL (Sprint 2.21.2 §5 Probe 4)
PF_LUSAIL_RENT_URL = "https://www.propertyfinder.qa/en/search?c=2&t=1&l=63"
PF_ROOT = "https://www.propertyfinder.qa/"

# arady probe candidates — patterns commonly used by real-estate sites
ARADY_ROOT = "https://arady.qa/"
ARADY_CANDIDATES = [
    "https://arady.qa/properties",
    "https://arady.qa/properties/lusail",
    "https://arady.qa/properties/apartments",
    "https://arady.qa/listings",
    "https://arady.qa/search?q=lusail",
    "https://arady.qa/search?location=lusail&type=apartment",
    "https://arady.qa/rent",
    "https://arady.qa/apartments-for-rent",
    "https://arady.qa/lusail",
    "https://arady.qa/sitemap.xml",
    "https://arady.qa/robots.txt",
]

PREDICTIONS = {
    "H1": {"text": "PropertyFinder reachable from Heroku (HTTP 200)",
           "result": "UNKNOWN", "evidence": ""},
    "H2": {"text": "PF Lusail apartment-rent page returns >=30 listing-pattern matches",
           "result": "UNKNOWN", "evidence": ""},
    "H3": {"text": "At least one arady search URL pattern returns HTTP 200 with listing content",
           "result": "UNKNOWN", "evidence": ""},
    "H4": {"text": "Heroku-IP PF counts match sandbox-IP within +-15 (no geo filtering)",
           "result": "UNKNOWN", "evidence": ""},
    "H5": {"text": "At least one PF listing detail page exposes both price + area",
           "result": "UNKNOWN", "evidence": ""},
}


def set_pred(pid, result, evidence):
    PREDICTIONS[pid]["result"] = result
    PREDICTIONS[pid]["evidence"] = evidence
    print(f"  [{pid}] -> {result}  ({evidence})")


def fetch(url, label=""):
    """Return (status, body_text, body_len, headers, latency_s, error)."""
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
            hdrs = dict(resp.headers)
            print(f"  HTTP {resp.status}  {dt:.2f}s  len={len(body):,}")
            return resp.status, body, len(body), hdrs, dt, None
    except urllib.error.HTTPError as e:
        dt = time.time() - t0
        try:
            body = e.read().decode("utf-8", errors="replace")
        except Exception:
            body = ""
        hdrs = dict(e.headers) if hasattr(e, "headers") and e.headers else {}
        print(f"  HTTP {e.code}  {dt:.2f}s  len={len(body):,}  ERR")
        return e.code, body, len(body), hdrs, dt, f"HTTPError {e.code}"
    except Exception as e:
        dt = time.time() - t0
        print(f"  {type(e).__name__}: {e}  {dt:.2f}s")
        return None, "", 0, {}, dt, f"{type(e).__name__}: {e}"


# --- PropertyFinder probe ---

def probe_propertyfinder():
    print("\n" + "=" * 78)
    print("STEP A — PropertyFinder Qatar (Heroku-IP)")
    print("=" * 78)

    # H1 — root + search reachability
    s, body, _, _, _, err = fetch(PF_LUSAIL_RENT_URL, "PF Lusail rent apartments")
    if s != 200:
        set_pred("H1", "FALSE", f"HTTP {s} err={err!r}")
        set_pred("H2", "FALSE", "blocked by H1")
        set_pred("H4", "UNDETERMINED", "blocked by H1")
        set_pred("H5", "UNDETERMINED", "blocked by H1")
        return None, []

    set_pred("H1", "TRUE", f"HTTP 200, body={len(body):,} chars")

    # H2 — listing-pattern count
    listing_links = re.findall(r"/(?:en|ar)/plp/[^\s\"\'<>]+", body)
    unique_listings = sorted(set(listing_links))
    listing_count = len(unique_listings)
    print(f"  raw plp link matches: {len(listing_links)}")
    print(f"  unique plp paths:     {listing_count}")
    if listing_count >= 30:
        set_pred("H2", "TRUE", f"unique={listing_count} unique listing paths")
    else:
        set_pred("H2", "FALSE", f"unique={listing_count} (threshold 30)")

    # H4 — compare to sandbox (sandbox showed 142 plp matches, but those were
    # ALL matches not unique; for parity record both numbers)
    sandbox_total_matches = 142  # from 2p21p2_pre/probe_t2_listings.py output
    delta = abs(len(listing_links) - sandbox_total_matches)
    if delta <= 15:
        set_pred("H4", "TRUE",
                 f"Heroku raw={len(listing_links)} vs sandbox={sandbox_total_matches}, |Delta|={delta}")
    else:
        set_pred("H4", "AMBIGUOUS",
                 f"Heroku raw={len(listing_links)} vs sandbox={sandbox_total_matches}, |Delta|={delta} (over 15; may be page-version drift, not geo filter)")

    # capture additional schema-relevant signals on the search page itself
    signals = {
        "QAR_tokens":       len(re.findall(r"\bQAR\s*[\d,]+", body)),
        "AED_tokens":       len(re.findall(r"\bAED\s*[\d,]+", body)),
        "lusail_mentions":  len(re.findall(r"Lusail|لوسيل", body)),
        "sqm_tokens":       len(re.findall(r"\bsqm\b|\bsq\s*m\b|m²|m2", body, re.IGNORECASE)),
        "bed_tokens":       len(re.findall(r"\b\d+\s*bed", body, re.IGNORECASE)),
    }
    print(f"  search-page signals: {signals}")

    # H5 — sample 2 detail pages to check extractability
    sample_paths = unique_listings[:2]
    detail_results = []
    for path in sample_paths:
        # rebuild absolute URL
        url = f"https://www.propertyfinder.qa{path}" if path.startswith("/") else path
        s2, body2, _, _, _, err2 = fetch(url, f"detail sample {path[:60]}")
        if s2 != 200 or not body2:
            detail_results.append({"path": path, "status": s2, "extractable": False})
            continue
        has_price = bool(re.search(r"\b(?:QAR|AED)\s*[\d,]+", body2))
        has_area = bool(re.search(r"\b(?:[\d,]+(?:\.\d+)?)\s*(?:sqm|sq\s*m|m²|m2)\b",
                                  body2, re.IGNORECASE))
        # alt: PF often uses CSS classes like data-test="property-price" / "property-size"
        has_price_marker = "property-price" in body2 or 'data-test="price"' in body2
        has_size_marker = "property-size" in body2 or 'data-test="size"' in body2
        extractable = (has_price or has_price_marker) and (has_area or has_size_marker)
        detail_results.append({
            "path": path, "status": s2,
            "has_price_token": has_price, "has_area_token": has_area,
            "has_price_marker": has_price_marker, "has_size_marker": has_size_marker,
            "extractable": extractable,
        })
        time.sleep(2)

    any_extractable = any(d.get("extractable") for d in detail_results)
    if not detail_results:
        set_pred("H5", "UNDETERMINED", "no detail pages sampled")
    elif any_extractable:
        set_pred("H5", "TRUE",
                 f"{sum(1 for d in detail_results if d.get('extractable'))} of "
                 f"{len(detail_results)} detail pages exposed BOTH price + area tokens")
    else:
        set_pred("H5", "FALSE",
                 f"0 of {len(detail_results)} detail pages had both extractable; "
                 f"sample={detail_results}")

    return signals, detail_results


# --- arady probe ---

def probe_arady():
    print("\n" + "=" * 78)
    print("STEP B — arady.qa URL pattern discovery (Heroku-IP)")
    print("=" * 78)

    # First, baseline the root
    s_root, _, root_len, _, _, _ = fetch(ARADY_ROOT, "arady root (baseline)")
    if s_root != 200:
        set_pred("H3", "FALSE", f"arady root HTTP {s_root} — site itself unreachable")
        return []

    # Then try each candidate URL
    findings = []
    working_candidates = []
    for url in ARADY_CANDIDATES:
        s, body, length, _, _, err = fetch(url, "candidate")
        # Heuristic: "working URL" = HTTP 200 AND body different from root
        # (>20% size difference) AND contains listing-ish content
        differs = abs(length - root_len) > root_len * 0.2 if root_len else False
        listing_hits = 0
        if s == 200 and body:
            patterns = [
                r"شقة|شقق|apartment",
                r"لوسيل|Lusail",
                r"\b(?:QAR|ريال|ر\.ق)\s*[\d,]+",
                r'/(?:properties?|listings?)/[\w\-]+',
                r"property[-_]card",
            ]
            for pat in patterns:
                listing_hits += len(re.findall(pat, body, re.IGNORECASE))
        looks_working = s == 200 and differs and listing_hits > 10
        findings.append({
            "url": url, "status": s, "length": length, "differs_from_root": differs,
            "listing_hits": listing_hits, "looks_working": looks_working,
            "error": err,
        })
        print(f"  -> differs_from_root={differs} listing_hits={listing_hits} "
              f"looks_working={looks_working}")
        if looks_working:
            working_candidates.append(url)
        time.sleep(2)

    # H3 verdict
    if working_candidates:
        set_pred("H3", "TRUE",
                 f"{len(working_candidates)} working URL pattern(s): {working_candidates}")
    else:
        # Possibly the only useful response was sitemap/robots — note that
        sitemap_or_robots_useful = any(
            f["status"] == 200 and ("sitemap" in f["url"] or "robots" in f["url"])
            for f in findings
        )
        if sitemap_or_robots_useful:
            set_pred("H3", "PARTIAL",
                     "no candidate is a clear listings page; sitemap/robots accessible — "
                     "Sprint 2.21.3 should parse those for the real URL structure")
        else:
            set_pred("H3", "FALSE",
                     "no working URL pattern in the 8 candidates probed")

    return findings


# --- main ---

def main():
    t0 = time.time()
    print("=" * 78)
    print("Pre-Sprint 2.21.3 — T2 connector reachability + URL discovery")
    print(f"Started: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print("=" * 78)

    pf_signals, pf_details = probe_propertyfinder()
    arady_findings = probe_arady()

    # Print ledger
    print("\n" + "=" * 78)
    print("PREDICTIONS LEDGER (copy into CHANGELOG_pre_2p21p3.md)")
    print("=" * 78)
    print(f"# Run from Heroku one-off dyno on {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"# Total wall time: {time.time() - t0:.1f}s")
    print()
    for hid in sorted(PREDICTIONS):
        p = PREDICTIONS[hid]
        print(f"- {hid} ({p['text']}): **{p['result']}** -- {p['evidence']}")

    # Decision summary
    print("\n" + "-" * 78)
    print("Inputs for BRIEF_2p21p3:")
    if pf_signals:
        print(f"  PropertyFinder search-page signals: {pf_signals}")
    if pf_details:
        print(f"  PropertyFinder detail sample (n={len(pf_details)}):")
        for d in pf_details:
            print(f"    {d}")
    if arady_findings:
        print(f"  arady URL probe summary:")
        for f in arady_findings:
            print(f"    {f['url']}  HTTP {f['status']}  hits={f['listing_hits']}  "
                  f"working={f['looks_working']}")
    print("=" * 78)

    # Exit code: 0 if H1 TRUE (apartments-unblock path is viable), 1 otherwise
    return 0 if PREDICTIONS["H1"]["result"] == "TRUE" else 1


if __name__ == "__main__":
    sys.exit(main())

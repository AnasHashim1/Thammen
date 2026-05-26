"""
pearl_t2_substitutes.py — fallback T2 source check after FGRealty 404

Goals:
  1. Confirm at least one of {PropertyFinder, Steps, QatarSale, arady} has
     Pearl Qatar apartment listings (satisfies the "traceable to real
     listing" half of Anas Delta Step 4 requirement).
  2. V3 incidental check: scan whatever pages we DO get for Huzoom-related
     tokens (satisfies SOURCE_EXCLUSIONS claim that Huzoom inventory is
     syndicated to T2 substitutes).
  3. Document outcomes for PHASE3_AUDIT report.

Read-only. No production state change.
"""
import json
import sys
import time
import urllib.request
import urllib.error

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

UA = "thammen-pre-2p22p0a-t2-substitute-check/1.0"
TIMEOUT = 30

PEARL_URLS = [
    # PropertyFinder Pearl Qatar
    ("propertyfinder", "https://www.propertyfinder.qa/en/buy/the-pearl/apartments-for-sale.html"),
    ("propertyfinder", "https://www.propertyfinder.qa/en/buy/the-pearl-qatar/apartments-for-sale.html"),
    # Steps Real Estate
    ("steps", "https://www.steps.qa/for-sale/apartments/the-pearl"),
    ("steps", "https://www.steps.qa/for-sale/the-pearl"),
    # QatarSale
    ("qatarsale", "https://www.qatarsale.com/properties/sale/apartments/the-pearl"),
    # arady
    ("arady", "https://arady.qa/listings?location=the+pearl&type=apartment"),
    ("arady", "https://arady.qa/the-pearl"),
]

PEARL_TOKENS = [
    "porto arabia", "qanat quartier", "viva bahriya", "floresta",
    "marsa malaz", "abraj quartier", "the pearl", "pearl qatar",
    "اللؤلؤة", "بورتو", "قنوات", "فيفا",
]
HUZOOM_TOKENS = ["huzoom", "هزوم"]


def fetch(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            return resp.status, raw, None
    except urllib.error.HTTPError as e:
        try:
            raw = e.read().decode("utf-8", errors="replace")
        except Exception:
            raw = ""
        return e.code, raw, f"HTTPError {e.code}"
    except Exception as e:
        return None, "", f"{type(e).__name__}: {e}"


def main():
    print("#" * 80)
    print(f"PEARL T2 SUBSTITUTE CHECK (after FGRealty 404)")
    print(f"Started: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}")
    print("#" * 80)
    results = []
    pearl_confirmed_on = []
    huzoom_confirmed_on = []
    for source, url in PEARL_URLS:
        print(f"  [{source}] {url}")
        status, raw, err = fetch(url)
        if err:
            print(f"    fail: {err}")
            results.append({"source": source, "url": url, "status": status, "error": err})
            continue
        lower = raw.lower()
        pearl_hits = [t for t in PEARL_TOKENS if t in lower]
        huzoom_hits = [t for t in HUZOOM_TOKENS if t in lower]
        print(f"    HTTP {status}, len={len(raw)}, pearl_tokens={pearl_hits}, "
              f"huzoom_tokens={huzoom_hits}")
        results.append({
            "source": source,
            "url": url,
            "status": status,
            "html_len": len(raw),
            "pearl_tokens_found": pearl_hits,
            "huzoom_tokens_found": huzoom_hits,
        })
        if pearl_hits:
            pearl_confirmed_on.append(source)
        if huzoom_hits:
            huzoom_confirmed_on.append(source)

    out = {
        "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "pearl_listings_confirmed_on": sorted(set(pearl_confirmed_on)),
        "huzoom_syndication_confirmed_on": sorted(set(huzoom_confirmed_on)),
        "all_attempts": results,
    }
    with open("pearl_t2_substitutes.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2, default=str)
    print()
    print("=" * 80)
    print("Pearl listings confirmed on T2 sources: "
          f"{sorted(set(pearl_confirmed_on)) or '(none)'}")
    print("Huzoom syndication confirmed on T2 sources: "
          f"{sorted(set(huzoom_confirmed_on)) or '(none — V3 unverified)'}")
    print("=" * 80)
    return 0 if pearl_confirmed_on else 1


if __name__ == "__main__":
    sys.exit(main())

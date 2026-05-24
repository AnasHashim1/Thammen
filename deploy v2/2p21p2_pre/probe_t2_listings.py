"""
Probes 3 + 4 of Sprint 2.21.2 §5 audit:

  Probe 3 — Does arady.qa have Lusail apartment listings (T2)?
            Pass: n>=30 listings retrievable.
  Probe 4 — Does PropertyFinder Qatar have Lusail apartment rent listings (T2)?
            Pass: n>=30 rent listings retrievable.

Reachability test only. Counts listing cards / result indicators. The
Sprint 2.21.3 connectors will handle proper extraction; this just
confirms "data exists in non-trivial quantity".
"""
import re
import sys
import time
import urllib.request
import urllib.error

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")
TIMEOUT = 20


def fetch(url, label):
    print(f"\n--- {label} ---")
    print(f"GET {url}")
    t0 = time.time()
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": UA,
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "en-US,en;q=0.9,ar;q=0.8",
        })
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            dt = time.time() - t0
            print(f"HTTP {resp.status}  {dt:.2f}s  len={len(body):,}")
            return resp.status, body
    except urllib.error.HTTPError as e:
        dt = time.time() - t0
        try:
            body = e.read().decode("utf-8", errors="replace")
        except Exception:
            body = ""
        print(f"HTTPError {e.code}  {dt:.2f}s  len={len(body):,}")
        return e.code, body
    except Exception as e:
        dt = time.time() - t0
        print(f"{type(e).__name__}: {e}  {dt:.2f}s")
        return None, ""


def count_signals(body, patterns, name):
    """Count regex matches per pattern. Useful for inferring listing count."""
    print(f"  Signal counts in {name}:")
    for desc, pat in patterns:
        n = len(re.findall(pat, body, re.IGNORECASE))
        print(f"    {desc!r:<40} {n}")


def probe_propertyfinder():
    # Lusail apartments for rent — PropertyFinder Qatar
    # Path pattern: /en/search?c=2&l=...&t=...
    # Public search page, SSR, well-documented to work
    candidates = [
        ("PF rent Lusail apartments",
         "https://www.propertyfinder.qa/en/search?c=2&t=1&l=63"),
        # alternate: simpler search root
        ("PF Qatar root",
         "https://www.propertyfinder.qa/"),
    ]
    for label, url in candidates:
        status, body = fetch(url, label)
        if status == 200 and body:
            patterns = [
                ("data-fbid / property-id attrs",   r'data-(?:fbid|propertyid|property-id)='),
                ("'/en/plp/' or '/ar/plp/' links",  r'/[ea][nr]/plp/[^"\']+'),
                ("'card-list__item' class",         r'card[-_]list__item'),
                ("'AED ' or 'QAR ' price tokens",   r'\b(?:AED|QAR)\s+[\d,]+'),
                ("'لوسيل' OR 'Lusail' mentions",    r'لوسيل|Lusail'),
            ]
            count_signals(body, patterns, label)
        if status == 200:
            break
    return status, body


def probe_arady():
    # arady.qa — Anas verified page-1 accessible (Operational §14)
    candidates = [
        ("arady Lusail apartments search (Arabic)",
         "https://arady.qa/properties?type=apartment&location=lusail"),
        ("arady root",
         "https://arady.qa/"),
    ]
    for label, url in candidates:
        status, body = fetch(url, label)
        if status == 200 and body:
            patterns = [
                ("property card class",            r'property[-_]card'),
                ("price token",                    r'\b(?:QAR|ريال|ر\.ق)\s*[\d,]+'),
                ("apartment Arabic 'شقة' or 'شقق'", r'شقة|شقق'),
                ("Lusail Arabic 'لوسيل'",          r'لوسيل'),
                ("listing link pattern",           r'/properties?/[\w-]+'),
            ]
            count_signals(body, patterns, label)
        if status == 200:
            break
    return status, body


def main():
    print("=" * 76)
    print("Probes 3 + 4 — T2 listing source reachability")
    print("=" * 76)

    print("\n>>> Probe 4 — PropertyFinder Qatar")
    pf_status, _ = probe_propertyfinder()

    print("\n>>> Probe 3 — arady.qa")
    ar_status, _ = probe_arady()

    print()
    print("=" * 76)
    print("INTERPRETATION (per BRIEF §5)")
    print("=" * 76)
    print(f"PropertyFinder reachable from this network: "
          f"{'YES' if pf_status == 200 else f'NO (HTTP {pf_status})'}")
    print(f"arady.qa reachable from this network:       "
          f"{'YES' if ar_status == 200 else f'NO (HTTP {ar_status})'}")
    print()
    print("NOTE: this probe runs from local sandbox, NOT Heroku. Heroku-IP "
          "reachability for Sprint 2.21.3 connectors will be confirmed in "
          "that Sprint's own smoke per section21.6. For Sprint 2.21.2 the only "
          "premise being tested is 'T2 data exists in non-trivial quantity' "
          "— answerable from any network with a working browser.")


if __name__ == "__main__":
    main()

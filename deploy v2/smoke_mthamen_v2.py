"""
Mthamen reachability smoke test v2 — WAF bypass attempts.

Previous result: HTTP 200 + F5 BIG-IP ASM rejection page.
This script tries 6 different User-Agent / Header combinations
to detect whether the WAF is permissive on any specific signature.

Usage:
    heroku run python smoke_mthamen_v2.py

Output: per-test status + summary at the end identifying which (if any) succeeded.
"""

import urllib.request
import urllib.error
import socket

URL = (
    "https://sak.gov.qa/pricingws/jsonstore1/"
    "PricingMobileDefBuildingStatusCRUD.ashx"
    "?action=getprices&squarid=1"
)

# Also test the root and a few simpler paths to map WAF behavior
PROBES = [
    ("https://sak.gov.qa/", "Site root"),
    ("https://sak.gov.qa/pricingws/", "Pricing service root"),
    (URL, "Main endpoint with params"),
]

# 6 different request profiles
PROFILES = [
    {
        "label": "1. Android Dalvik (original failure case)",
        "headers": {
            "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 12; Thammen)",
        },
    },
    {
        "label": "2. Mozilla Chrome browser (Windows)",
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/124.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "ar-QA,ar;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
        },
    },
    {
        "label": "3. iPhone Safari with Arabic locale",
        "headers": {
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) "
                          "AppleWebKit/605.1.15 (KHTML, like Gecko) "
                          "Version/17.0 Mobile/15E148 Safari/604.1",
            "Accept": "*/*",
            "Accept-Language": "ar-QA,ar;q=0.9",
            "Referer": "https://sak.gov.qa/",
        },
    },
    {
        "label": "4. No User-Agent at all",
        "headers": {},
    },
    {
        "label": "5. Android exact (mimicking the actual app)",
        "headers": {
            "User-Agent": "okhttp/4.9.0",
            "Accept-Encoding": "gzip",
            "Connection": "Keep-Alive",
            "Host": "sak.gov.qa",
        },
    },
    {
        "label": "6. With Qatar locale + referer + spoofed XFF",
        "headers": {
            "User-Agent": "Mozilla/5.0 (Linux; Android 12; SM-G991B) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/124.0.0.0 Mobile Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "ar-QA,ar;q=0.9,en-QA;q=0.8",
            "Referer": "https://sak.gov.qa/pricingws/",
            "Origin": "https://sak.gov.qa",
            "X-Forwarded-For": "212.77.192.1",  # known Qatar IP block (Ooredoo)
            "X-Real-IP": "212.77.192.1",
            "CF-IPCountry": "QA",
        },
    },
]

RESULTS = []


def is_waf_rejection(body_text: str) -> bool:
    """Detect F5 BIG-IP ASM rejection by signature."""
    return (
        "Request Rejected" in body_text
        or "support ID" in body_text
        or "Your support ID is" in body_text
    )


def test_profile(url: str, profile: dict) -> dict:
    """Run one test, return result dict."""
    try:
        req = urllib.request.Request(url, headers=profile["headers"])
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = resp.read()
            body_text = body.decode("utf-8", errors="replace")
            waf_rejected = is_waf_rejection(body_text)
            return {
                "ok": True,
                "status": resp.status,
                "ctype": resp.headers.get("Content-Type", "?"),
                "size": len(body),
                "waf_rejected": waf_rejected,
                "preview": body_text[:200],
            }
    except urllib.error.HTTPError as e:
        try:
            body = e.read()
            body_text = body.decode("utf-8", errors="replace")
        except Exception:
            body_text = ""
        return {
            "ok": False,
            "status": e.code,
            "ctype": "?",
            "size": 0,
            "waf_rejected": is_waf_rejection(body_text),
            "preview": f"HTTPError {e.code} {e.reason}: {body_text[:150]}",
        }
    except (urllib.error.URLError, socket.timeout, TimeoutError) as e:
        return {
            "ok": False,
            "status": 0,
            "ctype": "?",
            "size": 0,
            "waf_rejected": False,
            "preview": f"Network error: {type(e).__name__}: {e}",
        }
    except Exception as e:
        return {
            "ok": False,
            "status": 0,
            "ctype": "?",
            "size": 0,
            "waf_rejected": False,
            "preview": f"{type(e).__name__}: {e}",
        }


# ----------------------------------------------------------------------
# Phase 1: probe different paths with default headers
# ----------------------------------------------------------------------
print("=" * 75)
print("PHASE 1 — Path-level probes (basic headers)")
print("=" * 75)
basic_headers = {"User-Agent": "Mozilla/5.0", "Accept": "*/*"}
for probe_url, label in PROBES:
    res = test_profile(probe_url, {"headers": basic_headers})
    waf_flag = " 🛡️ WAF" if res["waf_rejected"] else ""
    print(f"\n  [{label}]{waf_flag}")
    print(f"    URL: {probe_url}")
    print(f"    → HTTP {res['status']}, {res['size']} bytes, {res['ctype']}")
    print(f"    Preview: {res['preview'][:120]!r}")


# ----------------------------------------------------------------------
# Phase 2: 6 different request profiles on the main endpoint
# ----------------------------------------------------------------------
print("\n" + "=" * 75)
print("PHASE 2 — Six WAF bypass attempts on main endpoint")
print("=" * 75)

for profile in PROFILES:
    print(f"\n  {profile['label']}")
    print(f"    Headers: {list(profile['headers'].keys()) or '(none)'}")
    res = test_profile(URL, profile)
    RESULTS.append((profile["label"], res))

    waf_flag = " 🛡️ WAF REJECTED" if res["waf_rejected"] else ""
    print(f"    → HTTP {res['status']}, {res['size']} bytes, {res['ctype']}{waf_flag}")
    print(f"    Preview: {res['preview'][:180]!r}")


# ----------------------------------------------------------------------
# Phase 3: summary
# ----------------------------------------------------------------------
print("\n" + "=" * 75)
print("SUMMARY")
print("=" * 75)

successes = [(label, res) for label, res in RESULTS
             if res["ok"] and not res["waf_rejected"] and res["status"] == 200]
waf_rejected = [(label, res) for label, res in RESULTS if res["waf_rejected"]]
other_failures = [(label, res) for label, res in RESULTS
                  if not res["waf_rejected"] and (not res["ok"] or res["status"] != 200)]

print(f"\n  Profiles bypassing WAF: {len(successes)}/{len(RESULTS)}")
print(f"  Profiles WAF-rejected:  {len(waf_rejected)}/{len(RESULTS)}")
print(f"  Other failures:         {len(other_failures)}/{len(RESULTS)}")

if successes:
    print("\n  ✓ WORKING PROFILE(S) — use these headers in mthamen_reference.py:")
    for label, res in successes:
        print(f"    • {label}")
        print(f"      Response: {res['preview'][:120]}")
    print("\n  → Next step: build Sprint 2.16.13 with working profile")
elif len(waf_rejected) == len(RESULTS):
    print("\n  ✗ ALL PROFILES BLOCKED by F5 ASM WAF.")
    print("  → Conclusion: header/UA tweaks insufficient. Likely geo-blocking")
    print("    or TLS fingerprinting (JA3/JA4). Need Path B (iPhone capture)")
    print("    or Path C (official API request to MoJ).")
else:
    print("\n  ⚠ Mixed results — see preview output above for clues.")

print()

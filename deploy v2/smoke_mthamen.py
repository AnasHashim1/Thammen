"""
Mthamen reachability smoke test — runs on Heroku to verify network access
to sak.gov.qa before building Sprint 2.16.13.

Usage:
    heroku run python smoke_mthamen.py

Three possible outcomes:
    1. HTTP 200 + JSON       → sak.gov.qa reachable, integration green-light
    2. HTTP 403 / blocked    → Heroku egress blocked; add sak.gov.qa to allowlist
    3. Rate limit message    → reachable but quota'd; need official API key from MoJ
"""

import urllib.request
import urllib.error
import json
import sys

URL = (
    "https://sak.gov.qa/pricingws/jsonstore1/"
    "PricingMobileDefBuildingStatusCRUD.ashx"
    "?action=getprices&squarid=1"
)

HEADERS = {
    "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 12; Thammen-SmokeTest)",
    "Accept": "application/json, text/html",
}

print("=" * 72)
print("MTHAMEN REACHABILITY SMOKE TEST")
print("=" * 72)
print(f"Target: {URL}")
print(f"Timeout: 15s")
print("-" * 72)

try:
    req = urllib.request.Request(URL, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=15) as resp:
        status = resp.status
        ctype = resp.headers.get("Content-Type", "unknown")
        body = resp.read()
        body_text = body.decode("utf-8", errors="replace")

        print(f"  STATUS: HTTP {status}  ✓ REACHABLE")
        print(f"  CONTENT-TYPE: {ctype}")
        print(f"  BODY SIZE: {len(body)} bytes")
        print("-" * 72)
        print("  RESPONSE PREVIEW (first 500 chars):")
        print()
        preview = body_text[:500]
        for line in preview.splitlines() or [preview]:
            print(f"    {line}")

        print()
        print("-" * 72)

        # Check for rate limit message
        if "تجاوزت الحد" in body_text:
            print("  ⚠ DETECTED: Daily rate limit message")
            print("    → Reachable but quota'd. Need official API key from MoJ.")
            sys.exit(2)

        # Try JSON parse
        try:
            data = json.loads(body_text)
            print("  ✓ Valid JSON received")
            print(f"  → Integration green-light. Build Sprint 2.16.13.")
            sys.exit(0)
        except json.JSONDecodeError:
            print("  ⚠ Response is reachable but not JSON")
            print(f"  → Inspect manually. May need different params.")
            sys.exit(1)

except urllib.error.HTTPError as e:
    print(f"  STATUS: HTTPError {e.code}  ✗ BLOCKED")
    print(f"  REASON: {e.reason}")
    try:
        err_body = e.read()[:500].decode("utf-8", errors="replace")
        print(f"  ERROR BODY: {err_body}")
    except Exception:
        pass
    print("-" * 72)
    if e.code == 403:
        print("  → Heroku egress proxy blocking sak.gov.qa.")
        print("    Action: contact Heroku support to add sak.gov.qa to egress")
        print("    OR: route through a proxy in your control")
    elif e.code in (502, 503, 504):
        print("  → sak.gov.qa server-side error (not your problem)")
        print("    Action: retry in a few minutes")
    else:
        print(f"  → Unexpected HTTP error code {e.code}")
        print(f"    Action: inspect response body above for clues")
    sys.exit(3)

except urllib.error.URLError as e:
    print(f"  STATUS: URLError  ✗ UNREACHABLE")
    print(f"  REASON: {e.reason}")
    print("-" * 72)
    reason_str = str(e.reason).lower()
    if "name or service not known" in reason_str or "name resolution" in reason_str:
        print("  → DNS failure. sak.gov.qa not resolvable from Heroku.")
        print("    Action: very unusual — contact Heroku support")
    elif "timeout" in reason_str or "timed out" in reason_str:
        print("  → Connection timeout. Network unreachable or firewalled.")
        print("    Action: probably egress blocking. Same as HTTP 403 case.")
    elif "connection refused" in reason_str:
        print("  → Server refused connection (port blocked / server down)")
    else:
        print(f"  → Unclassified network error. See reason above.")
    sys.exit(4)

except Exception as e:
    print(f"  STATUS: {type(e).__name__}  ✗ UNKNOWN ERROR")
    print(f"  DETAIL: {e}")
    sys.exit(5)

"""
probe_khazna_latency.py — Sprint 2.22.0a.5 (Bug A14) Phase 0 §0.4 distribution probe.

Goal: classify khazna QARS_Point response-time distribution as either
  (a) BIMODAL  — a fast-success cluster + a hard-fail/hang cluster, OR
  (b) SLOW-VALID MASS — a non-trivial fraction of responses that take many
      seconds yet return VALID features.

Decision rule (Anas, 2026-05-29):
  bimodal      -> H3 timeout bound is reversible / no Gate 2 -> proceed with code.
  slow-valid   -> bounding the timeout would convert slow-but-valid khazna answers
                  into legacy-fallback (different/older data) -> Gate 2 sign-off.

Single attempt per call (NO retry) so the raw per-call latency is visible.
Hardcoded endpoints + params replicate qatar_gis.find_property / get_plot exactly.
Run locally from a Qatari vantage (khazna geo-blocks US/EU, not Qatar).
Caveat (Rule #36/#39): local network latency is an additive constant vs the
Heroku->khazna path; the DISTRIBUTION SHAPE (bimodal vs slow-valid) is server-side
and therefore representative for the classification decision, not the absolute ms.
"""
import json
import time
import urllib.parse
import urllib.request
import urllib.error
import statistics

KHAZNA_BASE = "https://khazna.gisqatar.org.qa/fed/rest/services"
GIS_BASE = "https://services.gisqatar.org.qa/server/rest/services"
QARS = f"{KHAZNA_BASE}/QARS/QARS_Point/FeatureServer/0/query"
CADASTRE = f"{GIS_BASE}/Vector/CadastrePlots/MapServer/0/query"
DISTRICTS = f"{GIS_BASE}/Vector/Districts/MapServer/0/query"

UA = {'User-Agent': 'qatar-gis-py/2.0'}
PER_CALL_TIMEOUT = 30.0   # match production default; capture the full slow tail
REPS = 5
SLEEP = 0.3

# Real villa/building addresses (zone, street, building) from project docs.
ADDRS = [
    (56, 565, 21),   # Bou Hamour villa (multi-QARS) — the A14 anchor
    (52, 903, 90),   # safe anchor (apartment_building)
    (61, 875, 20),   # Public Works (subtype 6)
    (69, 329, 20),   # Fox Hills (Lusail)
    (70, 300, 25),   # diverse
    (53, 240, 12),   # diverse
]


def one_call(url, params):
    """Single attempt, no retry. Returns (elapsed_ms, outcome, n_features)."""
    enc = urllib.parse.urlencode(params)
    get_url = f"{url}?{enc}"
    if len(get_url) > 2000:
        req = urllib.request.Request(url, data=enc.encode('utf-8'), headers=UA)
    else:
        req = urllib.request.Request(get_url, headers=UA)
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=PER_CALL_TIMEOUT) as resp:
            raw = resp.read()
        dt = (time.perf_counter() - t0) * 1000.0
        if raw[:3] == b'\xef\xbb\xbf':
            raw = raw[3:]
        data = json.loads(raw.decode('utf-8'))
        if isinstance(data, dict) and data.get('error'):
            return dt, f"envelope_err({data['error'].get('code')})", 0
        feats = data.get('features', []) if isinstance(data, dict) else []
        return dt, ("ok" if feats else "empty"), len(feats)
    except urllib.error.URLError as e:
        dt = (time.perf_counter() - t0) * 1000.0
        reason = getattr(e, 'reason', e)
        tag = "timeout" if 'timed out' in str(reason).lower() else "urlerror"
        return dt, f"{tag}", -1
    except Exception as e:
        dt = (time.perf_counter() - t0) * 1000.0
        return dt, f"exc:{type(e).__name__}", -1


def qars_params(z, s, b):
    return {
        'where': f'ZONE_NO={z} AND STREET_NO={s} AND BUILDING_NO={b}',
        'outFields': '*', 'f': 'json',
        'returnGeometry': 'true', 'outSR': 4326,
    }


def summarize(label, samples):
    """samples: list of (elapsed_ms, outcome, n)."""
    print(f"\n===== {label} (n={len(samples)}) =====")
    ok = [d for d, o, n in samples if o == "ok"]
    valid = [d for d, o, n in samples if o in ("ok", "empty")]
    bad = [(d, o) for d, o, n in samples if o not in ("ok", "empty")]
    from collections import Counter
    outc = Counter(o for d, o, n in samples)
    print("  outcomes:", dict(outc))
    if valid:
        vs = sorted(valid)
        def pct(p):
            k = max(0, min(len(vs) - 1, int(round(p / 100.0 * (len(vs) - 1)))))
            return vs[k]
        print(f"  VALID-response latency ms: "
              f"min={vs[0]:.0f} p50={statistics.median(vs):.0f} "
              f"p90={pct(90):.0f} p95={pct(95):.0f} max={vs[-1]:.0f}")
        slow_valid = [d for d in vs if d >= 6000]
        print(f"  valid responses >=6000ms (slow-valid mass): "
              f"{len(slow_valid)}/{len(vs)} ({100.0*len(slow_valid)/len(vs):.0f}%)")
        if vs:
            print(f"  valid responses >=10000ms: "
                  f"{sum(1 for d in vs if d >= 10000)}/{len(vs)}")
    if bad:
        print(f"  failures: {len(bad)} -> {bad[:8]}")


def main():
    print("probe_khazna_latency.py — A14 Phase 0 distribution probe")
    print(f"per-call timeout={PER_CALL_TIMEOUT}s, reps={REPS}, single-attempt (no retry)")
    qars_samples = []
    print("\n--- raw QARS (khazna) calls ---")
    for (z, s, b) in ADDRS:
        for r in range(REPS):
            dt, outcome, n = one_call(QARS, qars_params(z, s, b))
            qars_samples.append((dt, outcome, n))
            print(f"  {z:>3}/{s:>3}/{b:<3} rep{r+1}: {dt:8.0f}ms  {outcome:<16} n={n}")
            time.sleep(SLEEP)
    summarize("KHAZNA QARS_Point", qars_samples)

    # Secondary: characterize the other sequential GIS stages (services.gisqatar)
    # for the request-budget timeout derivation (how many serial hops, each how slow).
    print("\n--- secondary GIS stages (services.gisqatar, 1 rep each) ---")
    sec = []
    for (z, s, b) in ADDRS[:3]:
        # districts spatial near a rough Doha point (cheap sanity timing only)
        dpar = {
            'where': '1=1', 'outFields': 'ANAME,DIST_NO', 'f': 'json',
            'returnGeometry': 'false', 'resultRecordCount': 1,
        }
        dt, o, n = one_call(DISTRICTS, dpar)
        print(f"  districts probe: {dt:8.0f}ms {o}")
        sec.append((dt, o, n))

    print("\nCLASSIFICATION HINT:")
    valid = sorted(d for d, o, n in qars_samples if o in ("ok", "empty"))
    if valid:
        slow = sum(1 for d in valid if d >= 6000)
        frac = 100.0 * slow / len(valid)
        if frac >= 10:
            print(f"  -> SLOW-VALID MASS ({frac:.0f}% of valid >=6s) ==> Gate 2 sign-off")
        else:
            fails = sum(1 for d, o, n in qars_samples if o not in ("ok", "empty"))
            print(f"  -> looks BIMODAL ({frac:.0f}% slow-valid; {fails} hard-fails) "
                  f"==> H3 bound reversible, proceed with code")
    else:
        print("  -> no valid responses captured (khazna unreachable from here?)")


if __name__ == "__main__":
    main()

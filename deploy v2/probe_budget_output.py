"""Safety check: does a budget-TRIP change the user-facing output (Gate 2 leak)?
Compare the full villa result vs the same call under a tight 3s budget. If the
tripped call returns a DIFFERENT valuation (degraded number) rather than the same
result / a clean refusal, v141 silently degrades output and must be fixed/reverted."""
import contextvars
import qatar_gis
import evaluate_unified as eu

ARGS = dict(zone=56, street=565, building=21, moj_csv_path='moj_weekly.csv',
            audience='buyer', use_listings=True, use_geo_v2=True)
KEYS = ('asset_type', 'valuation_amount', 'confidence', 'scope', 'status',
        'methodology', 'value_per_m2')


def snapshot(label, budget=None):
    def go():
        tok = qatar_gis.set_request_deadline(budget) if budget else None
        try:
            return eu.evaluate_thammen(**ARGS)
        finally:
            if tok:
                qatar_gis.clear_request_deadline(tok)
    r = contextvars.copy_context().run(go)
    print(f"\n[{label}] type={type(r).__name__}")
    if isinstance(r, dict):
        for k in KEYS:
            if k in r:
                print(f"   {k} = {r[k]}")
        print(f"   top-level keys: {sorted(r.keys())[:18]}")
    else:
        print("   (non-dict result)", repr(r)[:300])
    return r


full = snapshot("FULL (no budget)")
trip = snapshot("TRIPPED (budget=3s)", budget=3.0)

print("\n=== verdict ===")
if isinstance(full, dict) and isinstance(trip, dict):
    fv, tv = full.get('valuation_amount'), trip.get('valuation_amount')
    if tv is None and fv is not None:
        print("tripped → valuation suppressed (None) while full has a value: CLEAN-FAIL-ish")
    elif tv == fv:
        print("tripped valuation == full valuation: no degradation")
    else:
        print(f"!!! tripped valuation ({tv}) != full ({fv}) — DEGRADED OUTPUT (Gate 2 leak)")

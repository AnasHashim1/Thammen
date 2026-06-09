# Sprint 2.22.0b.10 — geometric-footprint isolated tests.
# Exercises the PRODUCTION function `_geometry_footprint` (Rule #40 / E14).
# Verifies: edge-pairing is rotation-safe (NOT bbox); is_rectangular gate +
# non-rect coverage-cap fallback; the setback/cap formula; R2 ceiling; degenerate
# guards; and the VALUE-INVARIANCE contract (return is display-only, never a value).
import sys, math
sys.stdout.reconfigure(encoding='utf-8')
from evaluate_unified import _geometry_footprint, SETBACK_FRONT_R1, SETBACK_SIDE_R1, SETBACK_REAR_R1

_pass = 0
_fail = 0
def check(cond, msg):
    global _pass, _fail
    if cond:
        _pass += 1
    else:
        _fail += 1
        print(f'  FAIL: {msg}')

def rect_ring(W, D, theta_deg=0.0, ox=1000.0, oy=2000.0):
    """A W×D rectangle ROTATED by theta (proves edge-pairing is rotation-safe;
    the axis-aligned bbox would be wrong for theta not in {0,90})."""
    th = math.radians(theta_deg)
    ux, uy = math.cos(th), math.sin(th)
    vx, vy = -math.sin(th), math.cos(th)
    p0 = (ox, oy)
    p1 = (ox + W * ux, oy + W * uy)
    p2 = (p1[0] + D * vx, p1[1] + D * vy)
    p3 = (ox + D * vx, oy + D * vy)
    return [list(p0), list(p1), list(p2), list(p3), list(p0)]  # closed ring

# legal setbacks (E15 corrected): front 5 / side 3 / rear 3
check((SETBACK_FRONT_R1, SETBACK_SIDE_R1, SETBACK_REAR_R1) == (5.0, 3.0, 3.0),
      'legal R1 setbacks must be front 5 / side 3 / rear 3')

# ── 1. rotated 36×18 rect (rotation-safety + envelope binds) ──
r = _geometry_footprint(rect_ring(36, 18, 37.0), 36 * 18, True, 0.60)
# env = max((36-8)*(18-6), (18-8)*(36-6)) = max(336, 300) = 336 ; cov_cap = .6*648 = 388.8 → 336
check(r is not None and r['method'] == 'setback_envelope', '36x18 method')
check(r and r['plot_dims_m'] == [36.0, 18.0], f'36x18 dims rotation-safe (got {r and r.get("plot_dims_m")})')
check(r and r['max_buildable_footprint_m2'] == 336, f'36x18 fp=336 (got {r and r.get("max_buildable_footprint_m2")})')

# ── 2. 30×30 square (matches probe 56/565/21 → 528, envelope binds) ──
r = _geometry_footprint(rect_ring(30, 30, 0.0), 900, True, 0.60)
check(r and r['max_buildable_footprint_m2'] == 528, f'30x30 fp=528 (got {r and r.get("max_buildable_footprint_m2")})')
check(r and r['method'] == 'setback_envelope', '30x30 method')

# ── 3. 30×35 (matches probe 55/296/13 → cov-cap 630 binds) ──
r = _geometry_footprint(rect_ring(30, 35, 18.0), 1050, True, 0.60)
# env = max((30-8)*(35-6),(35-8)*(30-6)) = max(638,648)=648 ; cov_cap=.6*1050=630 → min=630
check(r and r['max_buildable_footprint_m2'] == 630, f'30x35 cov-cap binds=630 (got {r and r.get("max_buildable_footprint_m2")})')

# ── 4. non-rectangular (is_rect=False) → coverage-cap fallback, dims None ──
penta = [[0, 0], [22, 0], [30, 12], [12, 20], [0, 14], [0, 0]]
r = _geometry_footprint(penta, 652, False, 0.60)
check(r and r['method'] == 'coverage_cap', 'non-rect method=coverage_cap')
check(r and r['plot_dims_m'] is None, 'non-rect dims None')
check(r and r['max_buildable_footprint_m2'] == round(0.60 * 652), f'non-rect fp=cov_cap 391 (got {r and r.get("max_buildable_footprint_m2")})')

# ── 5. is_rectangular True but ring not 4 pts → coverage-cap (graceful) ──
r = _geometry_footprint([[0, 0], [10, 0], [5, 9], [0, 0]], 600, True, 0.60)
check(r and r['method'] == 'coverage_cap', '3-pt ring falls to coverage_cap')

# ── 6. pdarea guards ──
check(_geometry_footprint(rect_ring(30, 30), None, True, 0.60) is None, 'pdarea None → None')
check(_geometry_footprint(rect_ring(30, 30), 0, True, 0.60) is None, 'pdarea 0 → None')

# ── 7. R2 ceiling (0.50) makes the coverage-cap bind tighter ──
r = _geometry_footprint(rect_ring(36, 18, 12.0), 648, True, 0.50)
# cov_cap = .5*648 = 324 < env 336 → 324
check(r and r['max_buildable_footprint_m2'] == 324, f'R2 cov-cap binds=324 (got {r and r.get("max_buildable_footprint_m2")})')

# ── 8. tiny plot: envelope ≤ 0 → coverage-cap (no crash / no negative) ──
r = _geometry_footprint(rect_ring(7, 5, 0.0), 35, True, 0.60)
check(r and r['method'] == 'setback_envelope' and r['max_buildable_footprint_m2'] == round(0.60 * 35),
      f'tiny plot env≤0 → cov_cap 21, no negative (got {r})')

# ── 9. VALUE-INVARIANCE contract: display-only keys, never a value ──
r = _geometry_footprint(rect_ring(36, 18), 648, True, 0.60)
check(set(r.keys()) == {'plot_dims_m', 'max_buildable_footprint_m2', 'method'},
      f'return keys are display-only (got {set(r.keys())})')
for forbidden in ('amount', 'value', 'low', 'high', 'adjustment_pct'):
    check(forbidden not in r, f'return must NOT carry value key {forbidden!r}')

# ── 10. it is a CEILING ≤ coverage cap (never exceeds the zone max) ──
for (W, D, area, cov) in [(36, 18, 648, 0.60), (30, 30, 900, 0.60), (40, 20, 800, 0.50)]:
    r = _geometry_footprint(rect_ring(W, D, 25.0), area, True, cov)
    check(r['max_buildable_footprint_m2'] <= round(cov * area) + 0,
          f'{W}x{D} fp must be ≤ coverage cap {round(cov*area)} (got {r["max_buildable_footprint_m2"]})')

print(f'\n2.22.0b.10 isolated: {_pass} passed, {_fail} failed')
sys.exit(1 if _fail else 0)

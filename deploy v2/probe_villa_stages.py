"""A14 follow-up: where does the heavy villa (56/565/21) time go, and does the
request budget actually bound it? Local (Qatar) — GIS is fast here, so totals are
small, but the STRUCTURE (cold vs warm MoJ; does a 3s budget bound the call?) is
what we need. Decides: GIS-only budget enough, or non-GIS / thread coverage gap."""
import time
import contextvars
import qatar_gis
import evaluate_unified as eu

ARGS = dict(zone=56, street=565, building=21, moj_csv_path='moj_weekly.csv',
            audience='buyer', use_listings=True, use_geo_v2=True)


def call():
    return eu.evaluate_thammen(**ARGS)


def timed(fn):
    t = time.perf_counter()
    err = None
    try:
        fn()
    except Exception as e:
        err = f"{type(e).__name__}: {e}"
    return time.perf_counter() - t, err


print("=== villa 56/565/21 local timing ===")
c, e1 = timed(call)
print(f"cold (incl MoJ parse): {c:6.2f}s  err={e1}")
w, e2 = timed(call)
print(f"warm (MoJ cached)    : {w:6.2f}s  err={e2}")
print(f"=> cold MoJ-parse + first-call overhead ~= {c - w:.2f}s")


def budgeted(seconds):
    tok = qatar_gis.set_request_deadline(seconds)
    try:
        return timed(call)
    finally:
        qatar_gis.clear_request_deadline(tok)


for b in (3.0, 1.0):
    el, err = contextvars.copy_context().run(lambda: budgeted(b))
    verdict = "BOUNDED ✓" if el <= b + 2.0 else "NOT bounded ✗ (budget misses this work)"
    print(f"budget={b}s -> elapsed {el:6.2f}s  {verdict}  err={err}")

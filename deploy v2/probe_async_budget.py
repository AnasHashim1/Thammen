"""Does the request-deadline contextvar survive the async-handler -> inline sync
call boundary the way FastAPI invokes it? If async loses the contextvar, the budget
set in api.py's `async def` handler is invisible to the engine on Heroku (explaining
the 30s 503 despite a 24s budget) — and the fix is to arm it in the SYNC engine entry."""
import asyncio
import time
import contextvars
import qatar_gis
import evaluate_unified as eu

ARGS = dict(zone=56, street=565, building=21, moj_csv_path='moj_weekly.csv',
            audience='buyer', use_listings=True, use_geo_v2=True)


def call():
    try:
        eu.evaluate_thammen(**ARGS)
    except Exception:
        pass


async def handler(budget):
    # mirrors api.py: set deadline in the async handler, call sync engine inline
    tok = qatar_gis.set_request_deadline(budget)
    try:
        t = time.perf_counter()
        call()
        return time.perf_counter() - t
    finally:
        qatar_gis.clear_request_deadline(tok)


el = asyncio.run(handler(1.0))
verdict = "context PRESERVED ✓ (async not the cause)" if el <= 3.0 else \
          "context LOST ✗ — budget invisible across async boundary"
print(f"async handler, budget=1.0s -> elapsed {el:6.2f}s  {verdict}")

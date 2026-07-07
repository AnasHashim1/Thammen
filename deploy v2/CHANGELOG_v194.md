# CHANGELOG v194 — Sprint 2.22.0b.114 «ترشيق الزمن: حفظ تحليل التواريخ + إصلاح تعطّل المسار السريع» (latency: _parse_date memoize + fast-classify crash fix)

**Engine:** `thammen-sprint2p22p0b114-latency-parsedate-memoize` · **SPRINT_TAG** `2.22.0b.114`
**Date:** 2026-07-07 · **Files:** `geo_reference_v2.py` (lru_cache import + the `_parse_date` decorator), `evaluate_unified.py` (the fast-classify except-handler crash fix + the 2 version lines) (+ `test_sprint_2_22_0b114.py`)
**Class:** 🟢 **VALUE-INVARIANT** — a pure-function memoize (identical output) + an error-path crash fix (only changes what happens when the fast path *already* failed). The 5-fixture villa byte-gate holds. `api.py` + `index.html` untouched. **The first slice of the PO-chosen «زمن الاستجابة أولاً» direction, audit-driven (Rule #51 / #33 — measured first).**

---

## 2. Why (the §5 latency audit — measured first, Rule #51)

The PO asked to attack response time. A cProfile audit of the warm villa path (56/565/21) split the cost:
- **Network (`urlopen`): ~7s** — the serial GIS chain (the known target; parallelizing it is Gate-2, determinism-gated per the Branch-B/§20.4 lessons → a separate audited sprint).
- **🔴 `geo_reference_v2._parse_date`: 5.4s cumulative over ~26,831 `strptime` calls** — a **pure-compute hotspot, NOT network.** MoJ transaction dates repeat massively across the ~26K-row pool, and each filter/sort/window pass re-parses them. `strptime` recompiles its format every call.

So ~⅔ of the warm compute time was redundant date-parsing — a value-invariant, zero-determinism-risk win, found only by measuring (the audit reshaped the plan: the low-hanging fruit was compute, not network).

**A pre-existing crash surfaced during the audit (bundled, #39):** on a transient fast-classify GIS flake the except handler at `evaluate_unified.py` did `print(..., file=sys.stderr)`, but `sys` is **shadowed** by later local `import sys` statements inside `evaluate_thammen` (module-level `import sys` at line 30; ~14 function-local `import sys` from line 4722) → the reference at line ~4290 raised **UnboundLocalError**, turning a recoverable fast-path flake into a **hard crash** instead of the intended defensive fall-through to the full pipeline. Bundled because it is on the exact heavy-GIS path this sprint targets, it is value-invariant (only the error path), and it was blocking the byte-gate verification (a transient flake crashed the eval mid-suite).

## 3. What this patch does

- **`geo_reference_v2._parse_date`** → `@lru_cache(maxsize=8192)` (+ `from functools import lru_cache`). The parse is a pure `str → datetime`; memoizing turns ~27K redundant `strptime` calls into O(1) dict lookups with **identical output**. `strptime` is KEPT (behavior-identical; the cache captures the repeated-call win). The profiler hotspot then disappears (5.4s → gone).
- **`evaluate_unified.py`** the fast-classify except handler → `print(f"[fast-classify] failed: {e}")` (drops the shadowed `file=sys.stderr`; logs to stdout, which Heroku captures) so the documented «fall through to full pipeline (defensive)» actually runs. A transient GIS flake in the fast path now recovers instead of crashing.

## 4. VALUE-INVARIANT

The memoize returns the same `datetime` for the same string (a pure function). The crash fix only changes the behavior when the fast path *already threw* (crash → graceful fall-through). No figure/method/rule/leadership touched; `api.py` + `index.html` untouched (only the engine memoize + error-path). The 5-fixture villa byte-gate is byte-identical.

## 5. Verification (measured)

- Isolated `test_sprint_2_22_0b114.py` **16/16** (E14: the REAL `_parse_date` — valid/whitespace/empty/None/invalid/garbage edges strptime-identical + cache identity + a registered cache HIT on a repeat; the `@lru_cache` decorator + `lru_cache` import; the fast-classify handler no longer references the shadowed `sys.stderr` + still logs+falls-through; the version format; **the 5-fixture villa byte-gate byte-identical end-to-end via the real engine**).
- **Audit before/after (cProfile, villa path):** `_parse_date` 5.4s cumulative (26,831 calls) → **eliminated from the profile top**; the warm villa amount **2,400,000 unchanged** (cold + warm); `urlopen` (network) is now the clear dominant remaining cost (~7s — the Gate-2 parallelization, deferred).
- **5-fixture villa byte-gate (real engine, live GIS): ALL BYTE-IDENTICAL** — 54/541/6 2.4M cost_led · 56/647/6 3.8M geo_full · 55/296/13 2.6M e25 · 56/565/21 2.4M matched · 52/903/90 refusal.
- DoD: aggregator **395/395 MATCH** · security **16/16** · surface-honesty **45/45** · broad walk **ALL GREEN** · py_compile OK.
- **R14 N/A by construction** — `index.html` + `api.py` untouched (backend-only; the served output renders identically — the §20.18 precedent).

## 6. Deployment

- Ritual: `git push origin master` FIRST, then `git subtree push --prefix "deploy v2" heroku master` (§20.112). Value-invariant → deploy-on-green after the live 5-fixture byte-gate.

## 7. Verification curl (post-deploy)

- `/api/health` → `3.1.0-sprint2.22.0b.114`.
- the 5-fixture villa byte-gate **byte-identical to v276** (value-invariant).
- warm villa response time observably lower (the compute hotspot removed; network unchanged).

## 8. What's NOT in this patch

- **The backend GIS-chain parallelization (~7s network)** — the durable latency fix, but **Gate-2 / determinism-gated** (the Branch-B/§20.4 lesson: parallelizing the GIS chain can change the central value if not proven byte-identical) → its own audited sprint with an H_det determinism harness.
- **The frontend honest-progress skeleton** (perceived latency during the ~7s network wait) — a separate value-invariant frontend slice.
- Sibling date-parse hotspots in `moj_reference`/`moj_db` (if any) — the profiler flagged only `geo_reference_v2._parse_date`; a follow-up can memoize twins if measured.
- The deeper `sys`-shadow cleanup (removing the ~14 redundant local `import sys` in `evaluate_thammen`) — the surgical line fix resolves the actual crash; the broad cleanup is a separate low-value refactor.

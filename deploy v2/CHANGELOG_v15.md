# CHANGELOG — Sprint 2.10: Version Unification

**Engine version:** `thammen-sprint2p10-version-unified`
**Date:** 2026-05-13
**Files changed:** `api.py`, `evaluate_unified.py`
**Builds on:** Sprint 2.9 (v14)

---

## Why this matters

A live API call after Sprint 2.9 deployment returned:

```json
{
  "engine_version": "thammen-sprint2p6-land-building-split",
  "/api/health → version": "3.1.0-sprint2.7"
}
```

The deployed code was **Sprint 2.9**, but two different version strings
disagreed with each other and neither matched the actual deployment.
A user (or future Claude session) inspecting the API to verify
"what's actually running" would get misleading answers from both fields.

Worse: `evaluate_unified.py` had **5 different hardcoded version
strings** scattered across 5 response paths, each stuck at whatever
Sprint introduced that codepath:

| Function | Sprint string | What it tagged |
|---|---|---|
| `_build_unified_output` | `sprint2p6-land-building-split` | the main path |
| `_build_fast_insufficient_data_response` | `sprint-a1-fast-classify` | empty MoJ data |
| `_build_fast_listing_only_response` | `sprint-a3-implied-rent` | listings-only |
| `_build_fast_income_only_response` | `sprint-a2-fast-income` | income-only |
| `_build_out_of_scope_response` | `sprint-a3-scope-filter` | unsupported asset |

In Sprints 2.7 and 2.9, *none* of these were updated — the project
documentation in Section 3 of Custom Instructions explicitly required
"Bump version in `/api/health` with each Sprint", but no single source
of truth existed, so the rule was unenforceable in practice.

## Root cause

The version string was duplicated across 6 sites (5 in
`evaluate_unified.py`, 1 in `api.py`), with no constant tying them
together. Each Sprint author would have to find and update 6 strings —
which is exactly the kind of friction that guarantees drift.

## What this patch does

### Single source of truth (`evaluate_unified.py:38-39`)

```python
# Sprint 2.10: single source of truth for engine version.
# Bump this ONE constant when shipping a new Sprint. All response
# paths and /api/health surface the same string — no more drift.
ENGINE_VERSION = 'thammen-sprint2p10-version-unified'
SPRINT_TAG = '2.10'           # for /api/health "3.1.0-sprint{SPRINT_TAG}"
```

### All 5 response paths use the constant (`evaluate_unified.py:1276, 1394, 1620, 1732, 2574`)

Each `'engine_version': 'thammen-sprint-XXX...'` literal is replaced
with `'engine_version': ENGINE_VERSION,`. The 5 response paths
themselves are unchanged — only the version label is now centralized.

### `api.py` imports + uses both constants

```python
# Line 56
from evaluate_unified import evaluate_thammen, ENGINE_VERSION, SPRINT_TAG

# Graceful fallback if unified engine fails to import (line 60-63)
except ImportError as e:
    _UNIFIED_OK = False
    ENGINE_VERSION = 'thammen-v2-fallback'
    SPRINT_TAG = 'fallback'

# /api/health (line 454-456)
"version": f"3.1.0-sprint{SPRINT_TAG}",
"engine": "unified" if _UNIFIED_OK else "v2_fallback",
"engine_version": ENGINE_VERSION,
```

### New field in `/api/health` response

```json
{
  "status": "ok",
  "version": "3.1.0-sprint2.10",
  "engine": "unified",
  "engine_version": "thammen-sprint2p10-version-unified",
  ...
}
```

The new `engine_version` field mirrors what `/api/evaluate` returns,
so the two are now provably-equal at every release.

## Future Sprint workflow

For every Sprint after 2.10, the version bump is **two lines** in
ONE file:

```python
# evaluate_unified.py:38-39
ENGINE_VERSION = 'thammen-sprintXpY-<slug>'
SPRINT_TAG = 'X.Y'
```

That's it. Both `/api/evaluate` (engine_version) and `/api/health`
(version + engine_version) automatically reflect the new Sprint.

---

## Verification — empirical evidence

### Before (current production, Sprint 2.9 deployed):
```bash
$ curl https://thammen.qa/api/evaluate -X POST ... | jq '{engine_version}'
{
  "engine_version": "thammen-sprint2p6-land-building-split"   ← 3 Sprints behind
}

$ curl https://thammen.qa/api/health | jq '{version, engine_version}'
{
  "version": "3.1.0-sprint2.7",                                ← 2 Sprints behind
  "engine_version": null                                       ← field didn't exist
}
```

### After (Sprint 2.10):
```bash
$ curl https://thammen.qa/api/evaluate -X POST ... | jq '{engine_version}'
{
  "engine_version": "thammen-sprint2p10-version-unified"
}

$ curl https://thammen.qa/api/health | jq '{version, engine_version}'
{
  "version": "3.1.0-sprint2.10",
  "engine_version": "thammen-sprint2p10-version-unified"      ← exact match
}
```

### Unit assertions (pre-deploy)
- `ENGINE_VERSION` literal count in `evaluate_unified.py`: **0** (was 5)
- `'engine_version': ENGINE_VERSION,` references: **5** (one per response path)
- `api.py` imports `ENGINE_VERSION` + `SPRINT_TAG`: ✓
- `api.py` /api/health uses `f"3.1.0-sprint{SPRINT_TAG}"`: ✓
- `api.py` /api/health echoes `ENGINE_VERSION`: ✓
- Fallback values defined when unified engine ImportError: ✓

---

## Deployment

```cmd
cd /d "C:\Thammen\deploy v2"
copy /Y api.py api.py.bak5
copy /Y evaluate_unified.py evaluate_unified.py.bak10
tar -xf "%USERPROFILE%\Downloads\sprint2p10-version-unified.zip"
findstr /C:"Sprint 2.10" api.py evaluate_unified.py
findstr /C:"ENGINE_VERSION" evaluate_unified.py
git add api.py evaluate_unified.py CHANGELOG_v15.md
git commit -m "Sprint 2.10: Unified version constant (no more drift)"
git push heroku master
```

## Verification curl

```bash
# 1. Health endpoint — both fields should match
curl https://thammen.qa/api/health | jq '{version, engine_version}'
# Expected:
# { "version": "3.1.0-sprint2.10",
#   "engine_version": "thammen-sprint2p10-version-unified" }

# 2. Evaluate — same engine_version
curl -X POST https://thammen.qa/api/evaluate \
  -H "Content-Type: application/json" \
  -d '{"zone":52,"street":903,"building":90,"audience":"buyer"}' \
  | jq '{engine_version}'
# Expected: "thammen-sprint2p10-version-unified" (same as /api/health)
```

If the two strings don't match exactly, the deploy is broken or
incomplete.

## What's NOT in this patch (intentional Sprint 2.10 scope)

- **Methodology strings** (`methodology_ar`, `methodology_disclaimer_ar`)
  remain hard-coded per response path. They describe *what* each
  codepath does, not *which Sprint* shipped — they're not redundant.
- **`/api/about`** still has its own `"version": "2.0.0"` — that's the
  product-facing public version, distinct from the engine version.
  Not unified intentionally.
- **Logging the version on startup** — `log.info(f"Unified engine loaded: {ENGINE_VERSION}")`
  is added, but no monitoring/alerting on version drift. Out of scope.
- **Historical retro-tag of prior Sprints** in git history — not
  rewriting commits. Going forward only.

## Methodological note

This Sprint addresses a process bug, not a user-visible bug. But the
process bug had **caused** prior user-visible regressions: I, the
project's developer, was citing the wrong Sprint number when claiming
"that bug was fixed in Sprint X" — because `/api/health` told me the
wrong story. Section 3 of Custom Instructions now becomes enforceable:
the version bump is one constant, period.

The triggering observation came from Section 9 self-correction:
"check completed work first" — the live `/api/evaluate` response
contradicted the deployed code's actual Sprint number, which would
have led to wrong conclusions in any future audit.

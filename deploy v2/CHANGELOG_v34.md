# CHANGELOG — Sprint 2.16.12: Housekeeping (B1 + B3)

**Engine version:** `thammen-sprint2p16p12-housekeeping-b1-b3`
**SPRINT_TAG:** `2.16.12` → /api/health reports `3.1.0-sprint2.16.12`
**Date:** 2026-05-18
**Files updated:** `api.py`, `evaluate_unified.py`, `evaluate_v3.py`
**Severity:** 🟡 Cleanup — closes two catalogued bugs that don't affect
output values but improve code quality and input validation.

---

## What this Sprint closes

Two long-open catalogued items from Section 18 of Project Instructions:

| ID | Title | Status |
|---|---|---|
| **B1** | Dead `sales_merge` import in `evaluate_v3.py` | ✓ closed |
| **B3** | `audience='hacker'` silently coerced to `'buyer'` | ✓ closed |

---

## B1 — Remove dead `sales_merge` import

### What was wrong

`evaluate_v3.py:72-76` carried this import block:

```python
try:
    from sales_merge import load_all_sales_xlsx, compute_trend_from_xlsx
    _SALES_AVAILABLE = True
except ImportError:
    _SALES_AVAILABLE = False
```

A grep across the whole codebase showed:
- `load_all_sales_xlsx` — never called
- `compute_trend_from_xlsx` — never called
- `_SALES_AVAILABLE` — never referenced

It was a leftover from an earlier idea (broker XLSX trend merging) that
never shipped. The `sales_merge.py` module itself contains 4 bare excepts
(lines 53, 57, 150, 189) — they were dormant because the module wasn't
actually being loaded into the runtime path.

### What this patch does

Replaces the try/except block in `evaluate_v3.py` with a 5-line comment
explaining the removal:

```python
# Sprint 2.16.12 (B1) — removed dead import block:
#     try:
#         from sales_merge import load_all_sales_xlsx, compute_trend_from_xlsx
#         _SALES_AVAILABLE = True
#     except ImportError:
#         _SALES_AVAILABLE = False
# Neither imported function nor _SALES_AVAILABLE was referenced anywhere
# in the codebase. sales_merge.py is left on disk for potential future
# use, but the unused try/except is no longer pulled into the import path.
```

`sales_merge.py` is left on disk unchanged — if a future Sprint reuses
the XLSX trend logic, it's still there. We're not deleting code, just
unwiring it.

### Impact

- One fewer import attempt at module load. No measurable speedup but
  one fewer surface for circular-import bugs.
- The 4 bare excepts in `sales_merge.py` remain harmless (file isn't
  loaded). If we ever rewire it, those should be tightened first.
- No behavioural change in any API response.

---

## B3 — Reject unknown audience values at the boundary

### What was wrong

`evaluate_unified.py:_normalize_audience()` (line 994) silently coerced
any unrecognized value back to `'buyer'`:

```python
def _normalize_audience(audience):
    ...
    if a in ('buyer', 'مشتري'):     return 'buyer'
    if a in ('seller', 'بائع'):     return 'seller'
    if a in ('investor', 'مستثمر'): return 'investor'
    return 'buyer'  # ← silent fallback for ANY unknown value
```

A user POSTing `audience='hacker'` got a buyer-tier brief with no error
signal. A typo like `audience='vauler'` or a deprecated alias also
quietly became buyer. The catalogued example was `audience='hacker'`
but the real concern is **typos masking misconfiguration in client
integrations** — a downstream tool silently using the wrong brief.

### What this patch does

Adds Pydantic `field_validator` on both request models with an explicit
whitelist:

```python
_AUDIENCE_ACCEPTED = frozenset({
    # canonical
    'buyer', 'seller', 'investor', 'valuer',
    # English aliases
    'valuator',
    # Arabic equivalents
    'مشتري', 'بائع', 'مستثمر',
    'مثمن', 'مثمّن', 'مُثمِّن',
    'مقيم', 'مقيّم', 'مُقيِّم',
})
```

Anything not in this set (or its case-folded form, for English) returns
HTTP 422 with a helpful message listing the accepted values. The engine's
`_normalize_audience()` is left in place — it now acts purely as an
alias resolver (Arabic → canonical, 'valuator' → 'valuer') rather than
a permissive coercer.

### Two-layer design rationale

1. **API boundary** (Pydantic, this Sprint): rejects unknown values.
   This is where input validation belongs.
2. **Engine internal** (`_normalize_audience`, unchanged): maps the
   accepted aliases to the 4 canonical names the brief generation
   code keys off. This stays because removing it would force every
   internal caller to canonicalize manually.

### Accepted values (full list)

| Audience | Canonical | Accepted forms |
|---|---|---|
| Buyer | `buyer` | `buyer`, `Buyer`, `BUYER`, `مشتري` |
| Seller | `seller` | `seller`, case variants, `بائع` |
| Investor | `investor` | `investor`, case variants, `مستثمر` |
| Valuer | `valuer` | `valuer`, `valuator`, case variants, `مثمن`, `مثمّن`, `مُثمِّن`, `مقيم`, `مقيّم`, `مُقيِّم` |

### Rejected (returns 422)

- Empty strings: `''`, `' '`
- Misspellings: `'vauler'`, `'mosaffer'`
- Other roles: `'admin'`, `'hacker'`, `'سمسار'` (broker — not in
  whitelist by design; brokers should pick a valuation audience)
- Wrong types: `123`, `['buyer']`, `{...}`

### Backward compatibility

- Any client sending one of the 17 accepted forms is **unaffected**.
- Any client sending an unknown value used to get a buyer-tier brief
  silently. They now get a 422 — that's the desired behaviour change.
- The default value (field omitted, or explicitly `None`) is still
  `'buyer'`.

---

## Version bump

```diff
-ENGINE_VERSION = 'thammen-sprint2p16p11-tower-sanity-carveout'
-SPRINT_TAG = '2.16.11'
+ENGINE_VERSION = 'thammen-sprint2p16p12-housekeeping-b1-b3'
+SPRINT_TAG = '2.16.12'
```

---

## Empirical verification (pre-deploy)

### Source sync check (5/5 passed)

```
✓ api.py imports field_validator
✓ api.py defines _AUDIENCE_ACCEPTED frozenset
✓ api.py defines _check_audience()
✓ api.py applies @field_validator('audience') to both request models
✓ evaluate_unified.py SPRINT_TAG bumped to 2.16.12
```

### B1 — dead import removed (1/1 passed)

```
✓ evaluate_v3.py has no live `from sales_merge import` line
✓ evaluate_v3.py has no live `_SALES_AVAILABLE = ...` line
✓ evaluate_v3.py still compiles after removal
✓ Sprint 2.16.12 (B1) comment marker present
```

### B3 — audience validator (28/28 passed)

```
Canonical English (must accept):
  ✓ buyer, seller, investor, valuer

Case variants (must accept):
  ✓ BUYER, Buyer, VALUER, Investor

English aliases (must accept):
  ✓ valuator, Valuator

Arabic equivalents (must accept):
  ✓ مشتري, بائع, مستثمر, مثمن, مقيم, مقيّم, مُثمِّن

Unknown values (must reject):
  ✓ hacker (the catalogued B3 case) → 422
  ✓ admin, typo, empty, whitespace → 422
  ✓ سمسار (Arabic, not in whitelist) → 422

None / default (must accept — backward compat):
  ✓ audience=None
  ✓ field omitted → defaults to 'buyer'

Non-string types (must reject):
  ✓ int, list, dict → 422
```

### Regression suite (46/46 passed)

```
test_stock_strata.py / test_scope_of_service.py / test_material_uncertainty.py
46 passed in 0.08s
```

### Lesson 1 — node --check on inline JS

```
✓ inline JS valid (no JS changes, but checked anyway per protocol)
```

### Lesson 2 — mobile viewport

Not applicable. No frontend changes.

---

## What this Sprint does NOT do

- **No engine behaviour change.** Same valuations, same briefs, same
  warnings. Only the boundary validation tightens.
- **No deletion of `sales_merge.py`.** The module is left on disk in
  case a future Sprint needs the XLSX trend merging logic. Only the
  unused import is removed.
- **No change to `_normalize_audience()` in evaluate_unified.py.** It
  stays as an alias resolver. The Pydantic validator handles rejection
  at the API boundary; the engine helper handles canonicalization
  internally.
- **No A2 fix** (Pydantic `extra='ignore'` lets unknown fields slip
  through). That's a separate catalogued item and would change client
  semantics more aggressively — kept for a later Sprint with deliberate
  client communication.
- **No B2 reopening.** Sprint 2.16.7 closed B2 (/api/evaluate accepting
  listing/rental). The new fields from Sprint 2.16.10 (unit_count,
  avg_monthly_rent_per_unit) flow through both endpoints, consistent.

---

## Deployment

```
prompt command
cd /d "C:\Thammen\deploy v2"
copy /Y api.py api.py.bak_2p16p11
copy /Y evaluate_unified.py evaluate_unified.py.bak_2p16p11
copy /Y evaluate_v3.py evaluate_v3.py.bak_2p16p11
tar -xf "%USERPROFILE%\Downloads\sprint2p16p12-housekeeping-b1-b3.zip"
findstr /C:"sprint2p16p12" evaluate_unified.py
findstr /C:"_AUDIENCE_ACCEPTED" api.py
findstr /C:"Sprint 2.16.12 (B1)" evaluate_v3.py
git add api.py evaluate_unified.py evaluate_v3.py CHANGELOG_v34.md test_sprint_2p16p12_b1_b3.py
git commit -m "Sprint 2.16.12: housekeeping — B1 (dead import) + B3 (audience whitelist)"
git push heroku master
```

## Post-deploy verification

1. **Health check:**
   ```
   curl https://thammen.qa/api/health
   ```
   Expected: `"version": "3.1.0-sprint2.16.12"`

2. **B3 — valid audience still works:**
   ```
   curl -X POST https://thammen.qa/api/evaluate ^
     -H "Content-Type: application/json" ^
     -d "{\"zone\":56,\"street\":565,\"building\":10,\"audience\":\"buyer\"}"
   ```
   Expected: `status: 200`, normal response.

3. **B3 — unknown audience rejected:**
   ```
   curl -X POST https://thammen.qa/api/evaluate ^
     -H "Content-Type: application/json" ^
     -d "{\"zone\":56,\"street\":565,\"building\":10,\"audience\":\"hacker\"}"
   ```
   Expected: `status: 422`, body contains `"audience must be one of..."`.

4. **B3 — Arabic valuer alias still works:**
   ```
   curl -X POST https://thammen.qa/api/evaluate ^
     -H "Content-Type: application/json" ^
     -d "{\"zone\":56,\"street\":565,\"building\":10,\"audience\":\"مثمّن\"}"
   ```
   Expected: `status: 200`, brief generated in valuer tier.

5. **B3 — typo (similar but wrong) rejected:**
   ```
   curl -X POST https://thammen.qa/api/evaluate ^
     -H "Content-Type: application/json" ^
     -d "{\"zone\":56,\"street\":565,\"building\":10,\"audience\":\"vauler\"}"
   ```
   Expected: `status: 422`. This is the desired behavioural change —
   used to silently become 'buyer'.

6. **B1 — no observable change** (it was dead code; the test is just
   that everything still works). The tower fix and compound regression
   from Sprint 2.16.11 must still produce identical results.

---

## Files in this patch

```
sprint2p16p12-housekeeping-b1-b3.zip
├── api.py                                  (MODIFIED: +30 lines)
├── evaluate_unified.py                     (MODIFIED: version bump only)
├── evaluate_v3.py                          (MODIFIED: removed 5-line import block)
├── test_sprint_2p16p12_b1_b3.py            (NEW: 34 isolated checks)
└── CHANGELOG_v34.md                        (NEW: this file)
```

---

## Updated bug catalogue (Section 18)

| ID | Severity | Status |
|---|---|---|
| A1 | 🔴 | ✓ closed (Sprint 2.16.6) |
| A2 | 🟡 | open — Pydantic extra=ignore |
| A3 | 🟡 | ✓ closed (Sprint 2.16.7) |
| A4 | 🟡 | ✓ closed (Sprint 2.16.7) |
| A5 | 🟡 | open — asset_type='unknown' UX |
| A6 | 🟠 | open — latency P95 ~25s (51/835/17 reference) |
| A7 | 🟡 | open — rics_compliant tier |
| A8 | 🟠 | open — comparable adjustments grid |
| A10 | 🟡 | ✓ closed (Sprint 2.16.7) |
| **B1** | 🟠 | ✓ **closed (this Sprint)** |
| B2 | 🟡 | ✓ closed (Sprint 2.16.7) |
| **B3** | 🟡 | ✓ **closed (this Sprint)** |
| Tower MUC missing | 🔴 | ✓ closed (Sprint 2.16.8 + 2.16.9) |
| Tower input ambiguity | 🔴 | ✓ closed (Sprint 2.16.10) |
| Tower sanity false-positive | 🟡 | ✓ closed (Sprint 2.16.11) |

**Open: 5** (A2, A5, A6, A7, A8). All three 🔴 critical are closed.

---

_Last updated: 2026-05-18 (Monday, 7th deploy today) — End of Sprint 2.16
series. Next development blocked on Thursday's confirmed-sales data._

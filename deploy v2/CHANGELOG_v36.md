# CHANGELOG v36 — Sprint 2.16.15: Pydantic `extra='forbid'` (Bug A2)

**Engine version:** `thammen-sprint2p16p15-extra-forbid`
**Date built:** 2026-05-19 (evening)
**Files changed:** `api.py`, `evaluate_unified.py`, `test_sprint_2p16p15_extra_forbid.py` (new)

---

## Why this matters

The two FastAPI request models (`EvaluateRequest`, `EvaluateDetailsRequest`)
used Pydantic's default `extra='ignore'`. That meant any field the model didn't
explicitly declare was **silently dropped** before reaching the engine.

The catalogued case (Bug A2 in Project_Instructions §18):

```http
POST /api/evaluate
{
  "zone": 51,
  "street": 835,
  "building": 17,
  "rental_inome": 30000      ← typo: should be rental_income
}
```

Pydantic accepted the payload, dropped `rental_inome`, and called
`evaluate_thammen(zone=51, street=835, building=17, rental_income=None)`.
The engine then took the "no income data" branch and returned a fast-path
`insufficient_data` response — while the user believed their 30K rent was
in the calculation.

This is the canonical *silent boundary failure*: the system behaves
exactly as if the field didn't exist, but the user has no signal anything
went wrong.

The same hazard covered:

- UI ↔ API drift (e.g. UI starts sending `listing_price` while API still
  expects `asking_price`).
- Arabic field names accidentally posted from a future Arabic-aware client.
- Fields meant for `/api/evaluate/details` posted to `/api/evaluate`
  (e.g. `floors`, `condition`) — the rich-input fields were silently
  ignored, producing a coarse "no building data" valuation.

Bug A2 was severity **Medium** because each individual misroute produces a
*defensible* (just suboptimal) valuation; the cost is methodological
silence, not a wrong number.

---

## Root cause

`api.py:240-294` (before this patch):

```python
class EvaluateRequest(BaseModel):
    zone: int
    street: int
    building: int
    audience: Optional[str] = 'buyer'
    asking_price: Optional[float] = Field(default=None, gt=0, lt=_ASKING_PRICE_MAX)
    rental_income: Optional[float] = Field(default=None, ge=0, lt=_RENTAL_INCOME_MAX)
    ...
    # no model_config → Pydantic v2 default = extra='ignore'

class EvaluateDetailsRequest(BaseModel):
    zone: int
    street: int
    building: int
    ...
    # same: extra='ignore' by default
```

Pydantic v2's default is `extra='ignore'` (matching v1 behavior). To reject
unknown keys with HTTP 422, `model_config = ConfigDict(extra='forbid')` must
be set explicitly.

---

## What this patch does

### Backend — `api.py`

1. **Import addition** (1 line):
   ```python
   from pydantic import BaseModel, ConfigDict, Field, field_validator
   ```

2. **`EvaluateRequest`** — first body line:
   ```python
   class EvaluateRequest(BaseModel):
       # Sprint 2.16.15 (Bug A2): reject unknown fields with HTTP 422 ...
       model_config = ConfigDict(extra='forbid')
       zone: int
       ...
   ```

3. **`EvaluateDetailsRequest`** — same pattern.

The change is **5 lines total** (1 import + 2 lines per model × 2 models).
No field-level constraints changed. The Sprint 2.16.12 `audience` validator
keeps working unchanged.

### Engine — `evaluate_unified.py`

`ENGINE_VERSION` and `SPRINT_TAG` bumped:

```python
ENGINE_VERSION = 'thammen-sprint2p16p15-extra-forbid'
SPRINT_TAG = '2.16.15'
```

No engine logic touched. The defense is purely at the API boundary.

### Frontend — `index.html`

**No changes.** The existing form fields all map to declared model fields,
so the UI behavior is identical for users who already submit valid payloads.

The only user-visible difference: a hand-crafted curl/Postman call with a
mistyped field now returns HTTP 422 with a message like:

```json
{
  "detail": [{
    "type": "extra_forbidden",
    "loc": ["body", "rental_inome"],
    "msg": "Extra inputs are not permitted",
    "input": 30000
  }]
}
```

The bad field is named in `loc[-1]` so any future UI can show "حقل غير
معروف: `rental_inome`" instead of generic "validation error".

---

## Verification — empirical evidence

### 1. py_compile (mandatory pre-deploy item #1)

```
api.py: OK
evaluate_unified.py: OK
```

### 2. Isolated logic tests for new code (mandatory item #5)

`test_sprint_2p16p15_extra_forbid.py` — **14/14 pass**:

```
A2 / EvaluateRequest — legal fields must still be accepted:
  ✓ minimal: zone+street+building
  ✓ with asking_price + rental_income
  ✓ with unit_count + per_unit (Sprint 2.16.10 tower path)
  ✓ with audience=investor

A2 / EvaluateRequest — unknown fields must be rejected (HTTP 422):
  ✓ typo: rental_inome (the catalogued A2 case)
  ✓ drift: listing_price (UI name) vs asking_price (API name)
  ✓ Arabic field name leak: الإيجار
  ✓ wrong endpoint: floors on /api/evaluate (belongs to /details)
  ✓ mixed: legal fields + 1 extra → still rejected

A2 / EvaluateDetailsRequest — legal fields must still be accepted:
  ✓ full villa input (Sprint 2.2/2.3)
  ✓ tower input (Sprint 2.16.10)

A2 / EvaluateDetailsRequest — unknown fields must be rejected:
  ✓ same typo on /details endpoint
  ✓ unknown random_param on /details

A2 / Error message must name the unknown field:
  ✓ ValidationError message names 'rental_inome'
```

Production-model round-trip (importing the real `api.py` classes,
not test replicas):

```
EvaluateRequest         model_config.extra = forbid
EvaluateDetailsRequest  model_config.extra = forbid
✓ EvaluateRequest rejects 'rental_inome': extra_forbidden on ['rental_inome']
✓ EvaluateDetailsRequest rejects 'random_field': extra_forbidden on ['random_field']
✓ EvaluateRequest accepts legal payload
✓ EvaluateDetailsRequest accepts legal payload
```

### 3. Regression suite (mandatory item #4)

```
test_stock_strata:           6/6  ✓
test_scope_of_service:      27/27 ✓
test_material_uncertainty:  13/13 ✓
test_sprint_2p16p14:        21/21 ✓
test_sprint_2p16p15:        14/14 ✓ (new)
─────────────────────────────────
                            81/81 passing
```

Sprint 2.16.14 baseline (67/67) preserved, plus 14 new A2 tests.

### 4. Mobile viewport (mandatory item #3) — N/A

No frontend changes. The existing 390×844 mobile layout (Sprint 2.16.4)
is untouched by this patch.

### 5. `node --check` on inline JS (mandatory item #2) — N/A

No `index.html` changes.

---

## Deployment

```
cd /d "C:\Thammen\deploy v2"
copy /Y api.py api.py.bak_2p16p14
copy /Y evaluate_unified.py evaluate_unified.py.bak_2p16p14
findstr /C:"thammen-sprint2p16p15-extra-forbid" evaluate_unified.py
findstr /C:"model_config = ConfigDict(extra='forbid')" api.py
git add api.py evaluate_unified.py test_sprint_2p16p15_extra_forbid.py CHANGELOG_v36.md
git commit -m "Sprint 2.16.15: Pydantic extra='forbid' (Bug A2)"
git push heroku master
```

### Post-deploy verification curl

Legal payload — must succeed:

```
curl -s -X POST https://thammen.qa/api/evaluate ^
  -H "Content-Type: application/json" ^
  -d "{\"zone\":51,\"street\":835,\"building\":17}" > legal.json
findstr /C:"thammen-sprint2p16p15-extra-forbid" legal.json
```

Typo payload — must return HTTP 422 with the bad field name:

```
curl -s -o typo.json -w "%%{http_code}" -X POST https://thammen.qa/api/evaluate ^
  -H "Content-Type: application/json" ^
  -d "{\"zone\":51,\"street\":835,\"building\":17,\"rental_inome\":15000}"
findstr /C:"rental_inome" typo.json
findstr /C:"extra_forbidden" typo.json
```

Expected:
- `legal.json` contains the engine_version string.
- `typo.json` returns 422 and contains both `rental_inome` and `extra_forbidden`.

---

## What's NOT in this patch

- **No change to field-level constraints** (`gt=0`, `ge=0`, `lt=` ceilings
  from Sprint 2.16.7 are preserved as-is).
- **No CLI hardening.** `evaluate_unified.py:main()` (the argparse path)
  doesn't go through Pydantic. CLI callers that pass `--rental -1000` still
  flow into `_check_input_sanity` and get a warning. This patch defends only
  the production HTTP boundary, where 100% of real users land.
- **No `_check_input_sanity` cleanup.** Negative-rental zeroing
  (recommendation #2 from today's audit) is a separate one-line surgical
  fix and is **not** bundled here — the marathon 2026-05-18 lesson was to
  keep each Sprint single-purpose. Filed for a follow-up Sprint.
- **No engine-side defense-in-depth.** `evaluate_thammen()` still uses
  Python keyword arguments; if a caller (e.g. a future internal script)
  bypasses FastAPI, unknown kwargs would raise `TypeError` (Python's
  default) rather than 422. That is correct behavior for the boundary
  case — only the HTTP entry point speaks the user-facing protocol.
- **No follow-up on mega try-block (recommendation #1).** That refactor
  has zero production telemetry to justify it; deferred until the next
  observability pass.

---

## Bug catalogue update

Move A2 from "🟡 Medium open" to "🟢 Resolved":

```
🟢 Resolved (12 → 13 bugs):
  A1, A2, A3, A4, A10, A11, B1, B2, B3, Tower CTA, MUC display, Tower
  input, Tower sanity
🟡 Medium open (3 → 2):
  A5  (asset_type: unknown بدون شرح)
  A7  (rics_compliant دائماً false)
```

Total resolved across all Sprints: **13**.
Critical open: **0**. High open: **2** (A6 latency, A8 comparable adjustments).

---

## Why this sequencing

Sprint 2.16.15 was originally reserved for the Confirmed Sales DB
integration (per Project_Instructions §11 and Session_Update §4). With
Anas's audit-driven discovery on 2026-05-19 evening of three open issues
in `evaluate_unified.py`, the surgical 5-line A2 fix was promoted to
2.16.15 because:

1. **Single-purpose**, 5-line patch — matches the 2026-05-18 marathon
   lesson.
2. **Zero regression risk** — purely additive at the API boundary; no
   engine logic changed.
3. **Closes a documented Medium bug** (A2) and unlocks better client error
   messages without waiting on the secretary's data.
4. **Independent of Thursday's data delivery**, so it doesn't compete with
   Confirmed Sales for cognitive bandwidth on Thursday.

Confirmed Sales DB integration is renumbered to **Sprint 2.16.16**
(Thursday 2026-05-21, when the secretary delivers historical sales).

---

*Sprint 2.16.15 — built 2026-05-19 evening.*

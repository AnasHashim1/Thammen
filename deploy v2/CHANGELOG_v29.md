# CHANGELOG — Sprint 2.16.7: Housekeeping Bundle (Validators + B2 + A10)

**Engine version:** `thammen-sprint2p16p7-housekeeping-validators`
**SPRINT_TAG:** `2.16.7` → /api/health reports `3.1.0-sprint2.16.7`
**Date:** 2026-05-18
**Files updated:** `api.py`, `property_factors.py`, `evaluate_unified.py`
**Severity:** 🔴 Critical bundle — closes A3 + B2 (both catalogued critical), plus A4 (high) and A10 (low)

---

## Why this matters — four catalogued bugs, single Sprint

This Sprint is the smallest possible patch that closes the highest-leverage
items in Section 18 of Project Instructions. None require new logic — all
four are missing-validation or missing-wiring problems exposed by direct
production probes on 2026-05-18 immediately after Sprint 2.16.6 stabilized.

### Live evidence (production, before this patch)

```
POST /api/evaluate   {"zone":69,"street":305,"building":201,
                      "asking_price": 5000000}
→ Status 200; response has NO asking_price field, NO comparison field.
  The value is silently dropped. (Bug B2)

POST /api/evaluate/details   {..., "asking_price": 0}
→ Status 200. Zero asking is accepted as a real listing price. (Bug A3)

POST /api/evaluate/details   {..., "asking_price": -1000000}
→ Status 200. Negative asking accepted; flows into comparison logic. (Bug A3)

POST /api/evaluate/details   {..., "rental_income": -1000}
→ Status 200. rental_income stored as -1000 in `active_listings`; 
  income_value is set to None but the raw negative value remains. (Bug A4)
```

### Why these survived this long

- **A3 + A4:** The Pydantic models used `Optional[float] = None` without 
  Field constraints. `0`, negatives, and absurd magnitudes (1, 999_999_999_999) 
  all passed validation. The engine has its own `None` guards for *missing* 
  values but not for *invalid* numeric values.
- **B2:** `/api/evaluate` (the "quick" endpoint) was originally address-only. 
  When `asking_price` and `rental_income` were added to the model in earlier 
  Sprints, they were threaded into `/api/evaluate/details` but the quick 
  endpoint was forgotten. API consumers calling the simpler endpoint silently 
  lost their listing data.
- **A10:** `تزوير` (forgery) was a typo for `تنظيم` (zoning regulation). 
  The label appeared only in the rare branch where a property's zoning code 
  was unrecognized — easy to miss in normal QA.

---

## What this patch does

### Change 1: `api.py` — import `Field` from pydantic

```diff
- from pydantic import BaseModel
+ from pydantic import BaseModel, Field
```

### Change 2: `api.py` — module-level sanity bounds

```python
# Sprint 2.16.7 — sanity bounds for monetary inputs (bug A3 + A4)
# Rationale: 500M QAR ceiling covers every realistic Qatar property
# (Lusail Marina Com-31 commercial tower at ~280M is near top of market).
# Rental income capped at 10M QAR/month covers any conceivable single asset.
_ASKING_PRICE_MAX = 500_000_000.0   # QAR
_RENTAL_INCOME_MAX = 10_000_000.0   # QAR/month
```

### Change 3: `EvaluateRequest` — accepts asking_price + rental_income (B2)

```diff
class EvaluateRequest(BaseModel):
    zone: int
    street: int
    building: int
    audience: Optional[str] = 'buyer'
+   asking_price: Optional[float] = Field(default=None, gt=0, lt=_ASKING_PRICE_MAX)
+   rental_income: Optional[float] = Field(default=None, ge=0, lt=_RENTAL_INCOME_MAX)
```

The fields are still **Optional**. Existing callers that don't send them
get identical behavior. Callers that DO send them now get the values
threaded through to the engine (Change 5).

### Change 4: `EvaluateDetailsRequest` — Field validators on monetary fields (A3 + A4)

```diff
-   asking_price: Optional[float] = None  # listing price (QAR)
-   rental_income: Optional[float] = None # monthly rental (QAR)
-   potential_rental: Optional[float] = None
+   asking_price: Optional[float] = Field(default=None, gt=0, lt=_ASKING_PRICE_MAX)
+   rental_income: Optional[float] = Field(default=None, ge=0, lt=_RENTAL_INCOME_MAX)
+   potential_rental: Optional[float] = Field(default=None, ge=0, lt=_RENTAL_INCOME_MAX)
```

**Bounds rationale:**
- `asking_price`: `gt=0` rejects 0, negatives, and zero-with-sign. 
  `lt=500M` rejects fat-finger inputs like 5_000_000_000.
- `rental_income`: `ge=0` allows 0 (a vacant unit being valued by income 
  approach with zero current rent is a legitimate case). Negatives rejected.
- `potential_rental`: same as `rental_income`.

Pydantic returns HTTP 422 with a structured error body when validation
fails — so callers immediately learn what they did wrong instead of
getting a meaningless 200 with their bad data invisibly absorbed.

### Change 5: `api.py:evaluate_quick` — wire listing_price + rental_income (B2)

```diff
            result = evaluate_thammen(
                zone=req.zone, street=req.street, building=req.building,
                moj_csv_path=str(MOJ_CSV),
                audience=req.audience or 'buyer',
+               # Sprint 2.16.7 (bug B2): wire through optional listing/rental
+               # so single-shot callers get comparison logic if they provide it.
+               listing_price=req.asking_price,
+               rental_income=req.rental_income,
                use_listings=True, use_geo_v2=True,
            )
```

This mirrors the pattern already in `/api/evaluate/details` (line 685–686).
The unified engine handles `None` gracefully, so callers who don't send the 
fields are unaffected.

### Change 6: `property_factors.py` — typo fix (A10)

Two occurrences of `تزوير` (forgery) → `تنظيم` (regulation/zoning):

```diff
-           name='zoning', label_ar=f'تزوير {zoning}',
+           name='zoning', label_ar=f'تنظيم {zoning}',
```

at lines 211 and 218 of `property_factors.py`. The label appears in the
`factors` array of reports under unrecognized or neutral zoning codes.

### Change 7: `evaluate_unified.py` — version bump

```diff
- ENGINE_VERSION = 'thammen-sprint2p16p6-classifier-v2-subtype-aware'
- SPRINT_TAG = '2.16.6'
+ ENGINE_VERSION = 'thammen-sprint2p16p7-housekeeping-validators'
+ SPRINT_TAG = '2.16.7'
```

---

## Empirical verification (pre-deploy, this container)

### Logic tests (22/22 passed) — `test_sprint_2p16p7_validators.py`

```
✓ api.py source matches test definitions (B2 wiring + validators)

Bug A3: /api/evaluate/details asking_price validation
  ✓ asking_price=0 -> 422
  ✓ asking_price=-1M -> 422
  ✓ asking_price=500M (at ceiling) -> 422
  ✓ asking_price=600M -> 422
  ✓ asking_price=1 (positive)
  ✓ asking_price=4.5M (typical villa)
  ✓ asking_price=280M (Com-31 tower)
  ✓ asking_price missing (Optional)

Bug A4: rental_income validation
  ✓ rental_income=-1000 -> 422
  ✓ rental_income=10M (at ceiling) -> 422
  ✓ rental_income=0 (vacant)
  ✓ rental_income=15K (typical villa)
  ✓ rental_income=1.5M (large compound)

Bug A4: potential_rental validation
  ✓ potential_rental=-500 -> 422
  ✓ potential_rental=0
  ✓ potential_rental=18K

Bug B2: /api/evaluate accepts asking_price + rental_income
  ✓ EvaluateRequest w/ asking_price=5M
  ✓ EvaluateRequest w/ rental_income=30K
  ✓ EvaluateRequest w/ both
  ✓ EvaluateRequest w/ neither (backward compat)
  ✓ EvaluateRequest w/ asking_price=-1 -> 422
  ✓ EvaluateRequest w/ asking_price=0 -> 422
```

The test file has a `verify_against_source()` function that re-reads
`api.py` and asserts the Field expressions match what the test defines.
If `api.py` drifts from the test, the test reports the mismatch.

### Regression suite (46/46 passed)

```
test_stock_strata.py ................................. PASS
test_scope_of_service.py ........................... PASS  
test_material_uncertainty.py ....................... PASS
46 passed in 0.84s
```

### Lesson 1 — `node --check` on extracted inline JS

```
Extracted 1 inline script blocks (49167 chars)
✓ inline JS syntactically valid
```

(no JS was changed in this Sprint, but per Section 5 of Project
Instructions this check runs every Sprint as a guard against incidental
break.)

### Lesson 2 — mobile viewport (390×844)

**Not applicable** — no CSS or form-shape changes in this Sprint. Forms
behavior unchanged on mobile.

---

## Backward compatibility

- **Old callers of `/api/evaluate`** (no asking_price/rental_income):
  unchanged. Optional fields, None default.
- **Old callers of `/api/evaluate/details`** sending valid values: unchanged.
- **Old callers of `/api/evaluate/details`** sending `asking_price=0` or 
  negatives: will now get **422 with a clear validation error** instead of 
  silently incorrect behavior. This is a **breaking change for bad inputs 
  only** — exactly the intent.
- **JavaScript frontend (index.html):** untouched. The frontend already 
  validates these fields client-side as `>0`; the server-side check is now 
  a true defense in depth.

---

## What is NOT in this patch

- **No new endpoint or feature.** Sanity + wiring only.
- **No engine changes.** `evaluate_thammen()` signature unchanged; the
  fields wired into `/api/evaluate` already existed in the engine — they
  just weren't passed from this handler.
- **No frontend changes.** index.html unchanged.
- **No fix for A2** (Pydantic `extra='ignore'` accepting unknown fields).
  Deferred — needs a separate decision about strict mode.
- **No fix for A5** (`asset_type: unknown` UX). Deferred — UX work, not
  housekeeping.
- **No fix for A6** (latency safety). Larger Sprint (2.18).
- **No fix for B1** (`sales_merge.py` dead import). Deferred to 2.18.
- **No fix for B3** (`audience='hacker'` accepted then coerced). Lower 
  priority — could be a separate validator next Sprint.

After this Sprint, the open-bug count in Section 18 drops from 11 to 7
(A1 already closed by 2.16.6).

---

## Deployment

```
prompt command
cd /d "C:\Thammen\deploy v2"
copy /Y api.py api.py.bak_2p16p6
copy /Y property_factors.py property_factors.py.bak_2p16p6
copy /Y evaluate_unified.py evaluate_unified.py.bak_2p16p6
tar -xf "%USERPROFILE%\Downloads\sprint2p16p7-housekeeping.zip"
findstr /C:"sprint2p16p7" evaluate_unified.py
findstr /C:"_ASKING_PRICE_MAX" api.py
findstr /C:"تنظيم {zoning}" property_factors.py
git add api.py property_factors.py evaluate_unified.py CHANGELOG_v29.md test_sprint_2p16p7_validators.py
git commit -m "Sprint 2.16.7: housekeeping bundle (A3+A4+B2+A10 closed)"
git push heroku master
```

## Post-deploy verification

1. **Health check (version bump):**
   ```
   curl https://thammen.qa/api/health
   ```
   Expected: `"version": "3.1.0-sprint2.16.7"` and
   `"engine_version": "thammen-sprint2p16p7-housekeeping-validators"`

2. **A3 verification — asking_price=0 must now be rejected:**
   ```
   curl -X POST https://thammen.qa/api/evaluate/details ^
     -H "Content-Type: application/json" ^
     -d "{\"zone\":69,\"street\":305,\"building\":201,\"asking_price\":0}"
   ```
   Expected: **HTTP 422** with body containing `"greater_than"` constraint.

3. **A3 verification — negative asking_price must now be rejected:**
   ```
   curl -X POST https://thammen.qa/api/evaluate/details ^
     -H "Content-Type: application/json" ^
     -d "{\"zone\":69,\"street\":305,\"building\":201,\"asking_price\":-1000000}"
   ```
   Expected: **HTTP 422**.

4. **A4 verification — negative rental_income must now be rejected:**
   ```
   curl -X POST https://thammen.qa/api/evaluate/details ^
     -H "Content-Type: application/json" ^
     -d "{\"zone\":69,\"street\":305,\"building\":201,\"rental_income\":-1000}"
   ```
   Expected: **HTTP 422**.

5. **B2 verification — asking_price now flows through /api/evaluate:**
   ```
   curl -X POST https://thammen.qa/api/evaluate ^
     -H "Content-Type: application/json" ^
     -d "{\"zone\":69,\"street\":305,\"building\":201,\"asking_price\":5000000}"
   ```
   Expected: HTTP 200, response now contains comparison/asking fields
   that were previously absent (compare to the same request before deploy).

6. **Backward compatibility — empty body still works on both endpoints:**
   ```
   curl -X POST https://thammen.qa/api/evaluate ^
     -H "Content-Type: application/json" ^
     -d "{\"zone\":69,\"street\":305,\"building\":201}"
   ```
   Expected: HTTP 200, normal evaluation response (no validation error).

7. **A10 verification — unrecognized zoning shows `تنظيم`:**
   Hard to trigger directly (most zoning codes are recognized), but a
   quick `findstr /C:"تنظيم" property_factors.py` post-deploy on the dyno
   would confirm. Visual confirmation on production not strictly needed —
   the typo affects a rare neutral-zoning branch only.

---

## Files in this patch

```
sprint2p16p7-housekeeping.zip
├── api.py                                (MODIFIED: ~15 line diff)
├── property_factors.py                   (MODIFIED: 2 char diff × 2 lines)
├── evaluate_unified.py                   (MODIFIED: 2 line diff — version bump only)
├── test_sprint_2p16p7_validators.py      (NEW: isolated validator tests)
└── CHANGELOG_v29.md                      (NEW: this file)
```

---

## Bug catalogue after Sprint 2.16.7

| ID | Severity | Status |
|---|---|---|
| A1 | 🔴 | ✓ closed (Sprint 2.16.6) |
| **A3** | 🔴 | ✓ **closed (this Sprint)** |
| **B2** | 🔴 | ✓ **closed (this Sprint)** |
| **A4** | 🟠 | ✓ **closed (this Sprint)** |
| **A10** | 🟢 | ✓ **closed (this Sprint)** |
| A2 | 🟡 | open (Pydantic extra=ignore) — deferred |
| A5 | 🟡 | open (asset_type: unknown UX) |
| A6 | 🟠 | open — Sprint 2.18 |
| A7 | 🟡 | open (rics_compliant tier) |
| A8 | 🟠 | open — Sprint 2.20 (largest gain) |
| B1 | 🟠 | open — Sprint 2.18 housekeeping |
| B3 | 🟡 | open (audience='hacker' coercion) |

Open bug count: 11 → 7. All 🔴 critical are now closed.

---

_Last updated: 2026-05-18 — Sprint 2.16.6 stabilized + housekeeping bundle. Next: 2.16.8 Tower UX (rental input + DCF flow + MUC clause) once Anas decides; or wait for confirmed sales data Thursday._

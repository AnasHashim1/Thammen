# CHANGELOG v40 — Sprint 2.21.0: PIN Input for Lands (activation)

**Engine version:** `thammen-sprint2p21p0-pin-input-lands`
**Date:** 2026-05-22
**Baseline:** Sprint 2.20.0 (`thammen-sprint2p20p0-time-adjustment-grid`, Heroku v79)
**Type:** Activation — make the deployed Land Grid (2.20) reachable. **Additive, non-destructive.**

**Files changed:**
- `qatar_gis.py` — `classify_asset(plot, location_metadata=None, input_mode=None)` + land branch; `full_property_lookup(... , pin=None, input_mode=None)` PIN entry
- `evaluate_property.py` — `evaluate_property(..., pin=None, input_mode=None)` pass-through
- `evaluate_unified.py` — `evaluate_thammen(..., pin=None, input_mode=None)` + PIN path in the quick block; threads input_mode to both classify_asset sites; ENGINE_VERSION → 2.21.0
- `api.py` — `pin` field on both request models; address-XOR-pin model validators (422 Arabic); pass `pin`/`input_mode='land'` through
- `index.html` — input-mode tab switcher (address | PIN) + PIN field (mobile)
- `docs/Operational_Rules.md` — Rule #46; `docs/Project_Instructions.md` — §4 + §11
- `tests/test_sprint_2p21_pin_lands.py` — new (21 checks); `tests/test_sprint_2p20_grid.py` — relaxed a self-inflicted version pin
- `probe_land_pins.py` — audit infra (committed v80)

---

## Why this matters

The Land Grid (2.20) shipped but was **unreachable**: the UI only accepted Z/S/B
(QARS, assigned post-construction → villas/buildings). Bare lands have a Cadastre
PIN but **no QARS address**. The pre-Sprint audit (§5) found two gaps (now
Rule #46):
1. **No UI path** for PIN entry.
2. **The classifier never returned land** — `classify_asset` typed a bare-land
   PIN as `standalone_villa` (high confidence). **Baseline probe: 0/5 known land
   PINs triggered the grid.**

→ The classifier fix was the PRIMARY change; PIN input was secondary.

---

## What this patch does

### Classifier (`qatar_gis.py`)
- `classify_asset` gains `input_mode`. A new branch (after the QARS-subtype branch,
  before the area heuristic) fires only when `input_mode=='land'` and no mapped
  subtype: `pdarea ≥50000 → COMPOUND_LARGE`, `≥15000 → COMPOUND_SMALL`, else
  **RAW_LAND**. Geometry overrides the user hint when conclusive. `input_mode=None`
  (every legacy caller) = behaviour byte-for-byte unchanged.

### Threading (linear chain)
- `api (pin → input_mode='land')` → `evaluate_thammen` → `evaluate_property` →
  `full_property_lookup` → `classify_asset`, **plus** the quick routing call in
  evaluate_unified. PIN entry skips `find_property` and resolves the plot via
  `get_plot(pin)`; a synthetic location (polygon centroid) keeps the district +
  MoJ-comparable gates working so `raw_land` reaches the full pipeline (it is in
  scope; not DCF-only). All params default `None` → additive.

### API (`api.py`)
- `pin: Optional[str]` (`^\d{7,9}$`) on both `EvaluateRequest` and
  `EvaluateDetailsRequest`; zone/street/building now Optional. A `model_validator`
  enforces **address XOR pin** → HTTP 422 with Arabic messages
  («…إحدى طريقتي الإدخال فقط…» / «…إما العنوان الكامل أو رقم القطعة»).

### Frontend (`index.html`)
- Tab switcher «فيلا/مبنى (عنوان)» | «أرض / قطعة (PIN)». Tab 1 unchanged. Tab 2 =
  PIN field (client `^\d{7,9}$`, Arabic label/help). Request body sends pin XOR
  z/s/b. Mobile-friendly (reuses the existing button-row layout).

---

## Decisions made (logged per Operational_Rules #39)

1. **Engine value = `raw_land`, NOT `'land'`** (deviation from the brief's "use
   'land'", forced by measured downstream reality, Rule #45): `AssetType` has only
   `RAW_LAND='raw_land'`; `ASSET_TYPE_TO_MOJ_CATEGORY` maps **`'raw_land'→'land'`**
   and has **no `'land'` key** → returning `'land'` would yield no MoJ category →
   break land valuation. The grid trigger accepts **both** `'land'` and
   `'raw_land'`, so `raw_land` satisfies the goal with zero downstream changes.
2. **Classifier fix is primary, PIN input secondary** — adding the field alone
   would have mis-typed lands as villas (Rule #46).
3. **Relaxed a self-inflicted version pin** in `tests/test_sprint_2p20_grid.py`
   (it asserted the frozen `2.20.0` literal — exactly the anti-pattern fixed in
   2.19.1). Now version-format-agnostic.

---

## Verification — empirical evidence

- **Baseline probe (Heroku v80, before fix):** `probe_land_pins.py` on the 5
  Anas-supplied land PINs → **0/5** grid_triggers (all `standalone_villa`, high
  conf). Confirms the gap.
- **After fix (local):** classifier matrix 21/21 — typical sizes → `raw_land`;
  ≥15K → compound_small; ≥50K → compound_large; `input_mode=None` unchanged
  (regression guard); QARS subtype still wins; API XOR 422 (both/neither/bad pin).
- **Full standalone suite: all 17 files exit 0.** `py_compile` clean on all
  modified Python.
- ⚠️ `node --check` could NOT run (Node not installed); the `index.html` change
  is a tab switcher + PIN field + tab-aware body — **browser-verify post-deploy**.
- **Post-deploy gate:** re-run `probe_land_pins.py` on the 5 PINs → expect **5/5**
  grid_triggers=YES; browser E2E on ≥2 PINs (grid renders, headline intact).

---

## Deployment

> **Not deployed in this session.** Awaiting explicit consent (Operational_Rules
> #32). When approved, from `C:\Thammen` per #43:

```
git subtree split --prefix "deploy v2" -b heroku-deploy-tmp
git push heroku heroku-deploy-tmp:master --force
git branch -D heroku-deploy-tmp
```

Rollback target (2.20.0) on Heroku = the v79 ref → `heroku rollback v79`.

## Verification curl / probe

```
curl -s https://thammen.qa/api/health | findstr /C:"sprint2p21p0"
heroku run python probe_land_pins.py 90040668 74328443 74430180 90421755 52060090
```

## What's NOT in this patch

- Apartment input (2.21.1, needs MME) · Commercial input (2.21.2) · map-based PIN
  picker (2.22.x roadmap) · default-tab memory · bulk PIN · PIN→address display.
- Size/corner adjustments (still 2.20.1 / E12). Villa Grid = 2.20.1 (reserved).

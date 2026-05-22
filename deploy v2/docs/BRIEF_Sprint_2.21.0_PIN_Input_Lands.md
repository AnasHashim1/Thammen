# Sprint 2.21.0 — PIN Input for Lands (ACTIVATION) — DRAFT for review

**Status:** DRAFT for review. **No code until approved** (Project_Instructions §5).
**Baseline:** Sprint 2.20.0 (`thammen-sprint2p20p0-time-adjustment-grid`, Heroku v79)
**Target:** Sprint 2.21.0 (`thammen-sprint2p21p0-pin-input-lands`)
**Type:** Activation — make the deployed Land Grid (2.20) reachable by users. **Additive, non-destructive.**
**Effort:** 1–2 days (classifier fix added scope).

---

## 0. Why this Sprint (audit trail, §5)

Sprint 2.20 Land Grid is deployed (v79) but **unreachable**: the UI only accepts
Z/S/B (QARS, assigned post-construction → villas/buildings). Bare lands have a
**Cadastre PIN but no QARS address**. The pre-Sprint audit found **two** gaps:

1. **(Anas) Backend works ≠ user can reach it** — no PIN input path in the UI.
2. **(audit) Classifier exists ≠ classifier returns the right type** —
   `classify_asset` ([qatar_gis.py:531-742](qatar_gis.py)) has **no branch that
   returns `land`/`raw_land`**. A bare 300–1500 m² parcel → **STANDALONE_VILLA**
   (Branch 6). Geometry (PDAREA/shape) **cannot** distinguish bare land from a
   villa lot. So even with a PIN field, the Land Grid (`asset_type ∈ {land,
   raw_land}`, [evaluate_unified.py:3080](evaluate_unified.py)) would never fire.

→ **The classifier fix is the PRIMARY change; PIN input is SECONDARY.** Both
codified in the expanded **Rule #46**.

---

## 1. Primary change — classifier `input_mode='land'` (HINT, not OVERRIDE)

`classify_asset(plot, location_metadata=None)` → add **`input_mode=None`** param.
A new branch runs **after** the subtype branch (Branch 0) and **before** the
area heuristic (Branch 1), so existing behaviour is unchanged when
`input_mode is None`:

```
if input_mode == 'land' and subtype is None:
    # geometry OVERRIDES the user hint when conclusive (compound, not raw land)
    if plot.pdarea >= 50000:            return COMPOUND_LARGE   (high conf)
    if plot.pdarea >= 15000:            return COMPOUND_SMALL   (medium)
    # accept user intent for typical land sizes
    return AssetType.LAND               (confidence per shape/subdivision)
# else: fall through to existing subtype / area heuristic unchanged
```

- **Naming:** output value = **`'land'`** (Anas's choice). Confirmed: the Land
  Grid trigger already accepts both `'land'` and `'raw_land'`
  ([evaluate_unified.py:3080](evaluate_unified.py)); CAP_RATES + geo `asset_to_cat`
  map both → land. **No naming harmonization needed.**
- **Geometric guards (Anas):** ≥50000 → compound_large; ≥15000 → compound_small;
  else land. (Note: slightly more conservative than the area heuristic's
  10000–50000 compound_small band — intentional for the land-hint path; documented.)
- **Safety:** purely additive — `input_mode=None` (every existing caller) →
  zero behaviour change. The 4/4-validated villa/building flow is untouched.

---

## 2. input_mode propagation (api → engine → classifier)

The hint must reach the **authoritative** asset_type determination, not just the
quick pre-classification:

- **api.py**: accept `pin` (Optional). When `pin` is provided, the request is a
  LAND request → pass `input_mode='land'` (or a `pin=` + derived flag) into
  `evaluate_thammen`.
- **evaluate_unified.evaluate_thammen**: add `pin` + `input_mode` params. When
  `pin` is set: **skip `find_property(z/s/b)`**, call `get_plot(pin)` directly,
  and pass `input_mode` to **every** `classify_asset(...)` call — at minimum the
  quick block ([evaluate_unified.py:2329-2349](evaluate_unified.py)) **and** the
  authoritative pipeline that sets the output `asset_type`. **Build task:** map
  ALL asset_type determination points and thread `input_mode` to the one the
  Land-Grid trigger reads. **Risk flagged:** if input_mode reaches only the quick
  block but not the authoritative `ev.asset_type`, the grid won't fire — E2E test
  (item §6.5) is the gate that catches this.
- The land path reuses the existing `get_plot → PlotInfo → classify_asset →
  geo_v2 (category='land') → comparable_grid` plumbing (all present).

---

## 3. API contract (validation)

`EvaluateRequest` / `EvaluateDetailsRequest` gain `pin: Optional[str]` with
`extra='forbid'` already enforced (Sprint 2.16.15). Rules:
- `pin` XOR (`zone`+`street`+`building`):
  - **both** present → **422**: «الرجاء استخدام إحدى طريقتي الإدخال فقط: العنوان أو رقم القطعة»
  - **neither** present → **422**: «الرجاء إدخال إما العنوان الكامل أو رقم القطعة»
- `pin` format: `^\d{7,9}$` (else 422 with a clear Arabic message).
- Field validators mirror the Sprint 2.16.12 audience-validator pattern.

---

## 4. Frontend (index.html) — tab switcher

- Tab switcher: **«فيلا/مبنى (عنوان)»** | **«أرض / قطعة (PIN)»**.
- **Tab 1** = existing Z/S/B form, **byte-for-byte unchanged**.
- **Tab 2** = single PIN field: label «رقم القطعة (PIN)», help «أدخل رقم القطعة
  من شهادة الملكية أو خرائط GIS», client-side `^\d{7,9}$`.
- Submit sends `{pin}` (Tab 2) or `{zone,street,building}` (Tab 1) — never both.
- **Mobile 390×844:** tabs render cleanly, no horizontal scroll (Sprint 2.16.4
  lesson). `node --check` unavailable locally → browser-verify post-deploy.

---

## 5. Files

| File | Change |
|---|---|
| `qatar_gis.py` | `classify_asset(plot, location_metadata=None, input_mode=None)` + land branch (PRIMARY) |
| `evaluate_unified.py` | `pin`/`input_mode` params; PIN→`get_plot` path; thread input_mode to classifier(s); ENGINE_VERSION → 2.21.0 |
| `api.py` | `pin` field + XOR validators (422 Arabic); pass through |
| `index.html` | tab switcher + PIN field (mobile) |
| `docs/Operational_Rules.md` | **Rule #46** (expanded) |
| `docs/Project_Instructions.md` | §4 — dual input flow (address \| PIN) |
| `tests/test_sprint_2p21_pin_lands.py` | new (classifier matrix + API validation) |
| `CHANGELOG_v40.md` | new |
| `probe_land_pins.py` | already written (audit infra) |

---

## 6. Validation gates

**Pre-build (needs Anas's 5 land PINs; run on Heroku — GIS unreachable from container):**
```
heroku run python probe_land_pins.py <PIN1..5>
```
1. CadastrePlots returns polygon for each (item 1).
2. classifier WITHOUT fix → expect **grid_triggers=NO** for all (baseline; item 2/3).
3. After classifier fix → repeat → **grid_triggers=YES** for typical lands.
4. Oversized parcel via land tab → still **compound_large/small** (guards work).

**Tests (`tests/test_sprint_2p21_pin_lands.py`, ≥6):**
- `classify_asset(plot, input_mode='land')`: 400-600 / 600-900 / 900-1500 m² → `land`.
- 15000 m² via land tab → `compound_small`; 60000 m² → `compound_large` (guards
  override the hint).
- `input_mode=None` → existing branches unchanged (villa-size → STANDALONE_VILLA)
  — **regression guard on the address flow**.
- subtype present + input_mode='land' → subtype branch still wins (hint ignored).
- API: pin-only → ok; pin+Z/S/B → 422; neither → 422; bad pin format → 422.
- Two-layer (Rule #40): real `classify_asset` + (where feasible) engine path.

**6.5 E2E (the whole point):** PIN input → `asset_type='land'` → Sprint 2.20
Land Grid renders. Verified on the 5 PINs from Heroku + browser (Arabic, mobile,
headline unchanged, console clean).

---

## 7. Rule #46 (to add to Operational_Rules)

> **#46 — Pre-Sprint frontend input-flow audit must validate classifier output
> for the NEW input path.** Two checks: (a) *backend feature exists ≠ user can
> reach it* (no UI path); (b) *classifier exists ≠ classifier returns the correct
> asset_type for the new input mode*. Lesson (2026-05-20, Sprint 2.21.0): the Land
> Grid (2.20) was deployed but unreachable, AND `classify_asset` would have
> labelled bare-land PINs as STANDALONE_VILLA. Pairs with #33, #45 and §5.

---

## 8. Out of scope / numbering
- Apartment input (2.21.1, needs MME) · Commercial input (2.21.2) · compound
  polygon detection improvements · map-based PIN picker · default-tab memory ·
  bulk PIN · PIN→address reverse display.
- **2.20.1 RESERVED** for the Villa Grid (Confirmed Sales era) — not used here.

---

## 9. Open items for sign-off
- Confirm classifier land-branch design + guard thresholds (50000 / 15000).
- Confirm `pin` lives on BOTH `EvaluateRequest` and `EvaluateDetailsRequest`.
- Awaiting Anas's **5 land PINs** (diverse districts/sizes, confirmed bare land)
  for the probe baseline + post-fix E2E.
- **No coding until this brief is approved.**

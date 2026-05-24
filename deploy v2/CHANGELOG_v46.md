# CHANGELOG v46 — Sprint 2.18.1.1 (Compound-misroute fix)

| field | value |
|---|---|
| **Engine version** | `thammen-sprint2p18p1p1-compound-misroute-fix` |
| **SPRINT_TAG** | `2.18.1.1` |
| **Date built** | 2026-05-23 evening (after Sprint 2.18.1 deploy + Anas's visual verification) |
| **Files changed** | `qatar_gis.py` (+42 lines in `full_property_lookup`), `evaluate_unified.py` (+28 lines in `_decompose_value` + version bump on lines 44-45) |
| **Files added** | `tests/test_sprint_2p18p1p1_compound_misroute.py` (7 functions, 19 sub-checks) |
| **Tests** | 19 new + 332 prior = **351 sub-checks** across **16/16 standalone files** (all exit 0). No regressions. |
| **Predecessor** | Sprint 2.18.1 (CHANGELOG_v45, Heroku v100 — parallel BFS upfront-prefetch) |
| **Rollback target** | Heroku v100 (`thammen-sprint2p18p1-parallel-bfs-prefetch`) |
| **Bug class closed** | Silent arithmetic failure on `compound_small` extents ≥ 15 K m² (land_value × area >> valuation_amount); universal `_decompose_value` guard for any future `land > valuation` divergence. |

---

## 1. Why this matters — the silent-failure that Sprint 2.18.1 unmasked

Sprint 2.18.1 cut the latency on 51/835/17 from 89 s → 29 s, converting **HTTP 503×3 → HTTP 200×3**. For the first time since the bug was catalogued, the engine's response for `compound_small` extents was actually reachable through the public API. Anas's verification step on the very next pass to thammen.qa caught what the 503 timeout had been masking for weeks:

```
Subject 51/835/17 (Public Works Authority compound, 67,536 m²):
  Total value:     6,800,000 QAR     ← MoJ median of similar transactions
  Land value:    218,073,744 QAR     ← 67,536 m² × 3,229 QAR/m²
  Building value: −211,273,744 QAR   ← total − land = silent negative
  Land %:           3,207 %
  Building %:      −3,107 %
  Status flag:    'land_exceeds_value'  (existed in code, not surfaced as refusal)
```

The compound_small valuation methodology silently composes two incompatible numbers when the extent area exceeds the MoJ-comparable sampling range:
- `valuation_amount` is the median of MoJ transactions for similar compounds — but MoJ's largest recorded "مجمع فلل" is **15,027 m²** (per Empirical_Findings audit). Applying that median to a 67 K m² compound stays anchored to ~6 M.
- `land_value = plot_area_m2 × land_per_m²` uses the FULL compound area linearly, regardless of comparable range — producing 218 M for the same compound.

The two diverge by 32× on 51/835/17, building_implied goes deeply negative, and the brief renders impossible percentages.

**This bug existed BEFORE Sprint 2.18.1.** It was always present, always silent, always returning broken numbers for any address whose compound extent exceeded ~15 K m². The HTTP 503 router timeout — caused by the serial BFS — had been masking it. Sprint 2.18.1 is not the cause; it is the **revealer**. The forensic credit goes entirely to Anas's post-deploy visual verification (CLAUDE.md §3 "Smoke test 3 diverse addresses from Heroku post-deploy").

---

## 2. Root cause — three cooperating defects in three modules

### Defect 1 — QARS subtype classifies COMPOUND_SMALL unconditionally
[qatar_gis.py:790-799](qatar_gis.py:790)

```python
SUBTYPE_TO_ASSET = {
    2:  AssetType.COMPOUND_SMALL,   # "Compound with Villas" → ALWAYS small
    3:  AssetType.COMPOUND_SMALL,   # "Compound with Villas and Flats"
    ...
}
```

The comment at line 793 *promises* "extent detection later can promote to COMPOUND_LARGE" — but **no such promotion existed**. For address-input compounds, the seed's QARS subtype dictated the type, and `_expand_extent`'s `total_area_m2` was never reflected back into reclassification.

### Defect 2 — `compound_small` routes through MoJ comparison
[evaluate_unified.py:2464](evaluate_unified.py:2464)

```python
DCF_ONLY = {'compound_large', 'tower', 'apartment_building'}   # ← compound_small missing
```

`compound_small` ∉ `DCF_ONLY`, so without rental_income the engine doesn't take the clean "insufficient_data" fast path. It proceeds to MoJ comparison + decomposition.

### Defect 3 — `_decompose_value` has no sanity guard
[evaluate_unified.py:828-846](evaluate_unified.py:828)

```python
land_value = round(plot_area_m2 * land_per_m2)        # 67,536 × 3,229 = 218 M
bld_implied = round(valuation_amount - land_value)    # 6.8 M − 218 M = −211 M
if bld_implied < 0:
    status = 'land_exceeds_value'                     # detected, not refused
    interp = 'القيمة المُقدَّرة أقل من قيمة الأرض ...'
# ... bad numbers still flow downstream
```

The code already detected the anomaly via the `land_exceeds_value` status — but it still RETURNED the broken numbers. The downstream brief rendered the impossible percentages.

### Composition trail for 51/835/17

1. Address → QARS lookup → subtype=2 → **Defect 1**: classified `compound_small` (regardless of 67 K extent)
2. `compound_small` ∉ `DCF_ONLY` → routes to full MoJ pipeline → **Defect 2**: no clean refusal
3. `_decompose_value(67536, 3229, 6.8M)` → land=218 M, building=−211 M → **Defect 3**: no sanity guard

Fixing any **one** would prevent the user-visible bug. Sprint 2.18.1.1 fixes **two** (Patches A + C) for defence-in-depth; defect 2 (the DCF_ONLY membership) is addressed *indirectly* by Patch A's promotion (the now-compound_large asset_type lands in DCF_ONLY via the established compound_large code path).

---

## 3. What this patch does (Patches A + C, single Sprint per Rule #38)

### Patch A — extent-driven classifier promotion

[qatar_gis.py:1933-1972](qatar_gis.py:1933) (`full_property_lookup`):

After `classify_asset` + `detect_extent`, if both:
- `classification.asset_type == AssetType.COMPOUND_SMALL`
- `extent.total_area_m2 ≥ 15_000`

→ Mutate `classification.asset_type` to `AssetType.COMPOUND_LARGE` (and mirror on `extent.asset_type`). Confidence downgraded to `medium`. Audit-trail note appended to both `classification.reasons` and `extent.notes`:

```
Sprint 2.18.1.1: extent total {N:,.0f} m² ≥ 15,000 — promoted compound_small
→ compound_large. MoJ has no comparable "مجمع فلل" transactions at this scale
(max observed = 15,027 m²); Income Approach with rent input is the only
valid methodology.
```

**Mechanism**: `evaluate_property.py:191` already has `ASSET_TYPE_TO_MOJ_CATEGORY['compound_large'] = None`. With the promotion in place, the MoJ comparison skips (line 1467) → `valuation = None` → clean refusal — IDENTICAL to the established compound_large via PIN behaviour (which my §5/C probe confirmed already returns `valuation_amount=None`).

### Patch C — defensive sanity guard in `_decompose_value`

[evaluate_unified.py:828-857](evaluate_unified.py:828):

```python
land_value = round(plot_area_m2 * land_per_m2)

# Sprint 2.18.1.1 — Patch C: defensive sanity guard
if land_value > valuation_amount:
    return None
```

**Universal** — not compound-specific (per Anas's scope decision #4). Three classes of bug this catches:
1. Compound misroute (the trigger; primarily caught by Patch A — this is belt-and-suspenders).
2. Premium-land teardown candidates: small old villas on Pearl / Lusail (~7 K QAR/m²) where land × area > as-built valuation. Sprint 2.16.10-era Lusail B201 dynamics.
3. MoJ sample outliers pulling the bracket median below land truth (rare but possible on small brackets, n<10).

Frontend at [index.html:862](index.html:862) `if(hasValuation && v.value_decomposition)` naturally skips the broken tile when `value_decomposition` is absent — no UI code change needed.

### What is intentionally NOT in scope

- The original Arabic `interp` string for the `land_exceeds_value` status (lines 848-852 of pre-patch) is **not surfaced separately** in this Sprint. If Anas later wants it bubbled into `sanity_warnings`, that's a 3-line follow-up (separate Sprint per Rule #38).
- New COMPOUND_MEDIUM enum tier (Anas's scope decision #1: 2-tier suffices, no COMPOUND_MEDIUM).
- Adding `compound_small` to `DCF_ONLY` set in evaluate_unified.py (Patch A's promotion accomplishes the same routing for the only case that matters — extent ≥ 15 K — and leaves <15 K compounds with their working MoJ comparison path unchanged).
- Latency, performance, or other concerns.

---

## 4. Files modified

| file | lines added / changed | what |
|---|---:|---|
| `qatar_gis.py` | +42 in `full_property_lookup` (~lines 1933-1972) | Patch A: promotion check + classification + extent mutation + audit note |
| `evaluate_unified.py` | +28 in `_decompose_value` (~line 828) | Patch C: 1 functional line + 26 lines of inline documentation |
| `evaluate_unified.py` | 2 (lines 44-45) | Version bump to `2.18.1.1` |
| `tests/test_sprint_2p18p1p1_compound_misroute.py` | new, 354 lines | 7 functions, 19 sub-checks |

---

## 5. Expected impact (audit-derived prediction — Rule #51)

### 5.1 The trigger case

| metric | v100 (pre-2.18.1.1) | v101 predicted | source |
|---|---|---|---|
| 51/835/17 asset_type | `compound_small` (wrong) | **`compound_large`** | Patch A promotion (extent = 67 536 m² ≥ 15 K) |
| 51/835/17 `classification.confidence` | (varies) | **`medium`** | Patch A downgrades confidence |
| 51/835/17 `valuation_amount` | 6 800 000 (wrong) | **`None`** | `ASSET_TYPE_TO_MOJ_CATEGORY['compound_large']=None` skip |
| 51/835/17 `value_decomposition` | `{land: 218 M, building: −211 M, ...}` (silent failure) | **(absent / `None`)** | No valuation → no decomposition; Patch C extra guard |
| 51/835/17 `verdict` | (likely DCF_REQUIRED, untested) | **`DCF_REQUIRED`** | evaluate_property line 1162-1168 |
| 51/835/17 HTTP status | 200 (with broken numbers) | **200** (with clean refusal + "needs rent input" Arabic message) | Unchanged HTTP-wise |
| 51/835/17 latency | ~29 s | **~29 s** (this Sprint adds 0 GIS calls) | Patch A is pure-Python comparison |

### 5.2 Regression checks (3 cases — must NOT change)

| case | v100 expected | v101 expected | reason |
|---|---|---|---|
| safe_villa_52 (52/903/90) | HTTP 200, fast-path, ~4 s, `apartment_building` | UNCHANGED | apartment_building never enters `_expand_extent` |
| multi_qars_56 (56/565/21) | HTTP 200, ~23 s, `standalone_villa`, MoJ comparison + value_decomposition | UNCHANGED | extent = single-PIN size << 15 K, Patch A doesn't fire; land/value sanely related, Patch C doesn't fire |
| PIN 66030258 (compound_large via PIN) | HTTP 200, ~4.5 s, `unknown` (asset_type_reality stop), `valuation_amount=None` | UNCHANGED | PIN path doesn't reach `_expand_extent` promotion (already stopped by reality-check) |

### 5.3 Probe verification target

Post-deploy, re-run `probe_compound_classifier_bug.py` against v101. Expected output:

```
=== a6_trigger_51 (address) ===
  asset_type       =          compound_large   ← was 'compound_small'
  plot_area_m2     =                   67536.0 ← unchanged
  valuation_amount =                      None ← was 6,800,000
  land_per_m2      =                      None ← was 3,229
  land_value       =                      None ← was 218,073,744
  building_value   =                      None ← was −211,273,744
  decomp_status    =                      None ← was 'land_exceeds_value'
  SILENT FAILURE detector: (no longer triggers — land_value=None)
```

Acceptance gate: any one of the following = hard failure → rollback to v100:
- `asset_type` still `compound_small`
- `valuation_amount` not `None`
- `value_decomposition` present (with or without land tile)
- Regression case fails (any of the 3 control cases shows any change in asset_type / valuation_amount / HTTP status)

---

## 6. Post-deploy measurement (actual)

*To be filled after deploy — Rule #51 step 3.*

### 6.1 The trigger case

| field | v100 measured | v101 predicted | v101 actual | verdict |
|---|---|---|---|---|
| `asset_type` | compound_small | compound_large |  |  |
| `valuation_amount` | 6 800 000 | None |  |  |
| `land_value` | 218 073 744 | None |  |  |
| `building_value` | −211 273 744 | None |  |  |
| `decomp_status` | land_exceeds_value | None |  |  |
| `classification.confidence` | (varies) | medium |  |  |
| HTTP status | 200 | 200 |  |  |
| Latency | ~29 s | ~29 s (±5 %) |  |  |

### 6.2 Regression checks

| case | v100 | v101 actual | verdict |
|---|---|---|---|
| safe_villa_52 | 200 / ~4 s / apartment_building | | |
| multi_qars_56 | 200 / ~23 s / standalone_villa / decomp present | | |
| PIN 66030258 | 200 / ~4.5 s / unknown / valuation_amount=None | | |

---

## 7. Deployment

Per Operational_Rules #43 (Heroku app lives in `deploy v2/` subdir of `C:\Thammen`):

```
cd /d "C:\Thammen\deploy v2"
git add qatar_gis.py evaluate_unified.py tests/test_sprint_2p18p1p1_compound_misroute.py CHANGELOG_v46.md
git commit -m "Sprint 2.18.1.1: compound-misroute fix (Patches A + C)"

cd /d C:\Thammen
git subtree split --prefix "deploy v2" -b heroku-deploy-tmp
git push heroku heroku-deploy-tmp:master --force
git branch -D heroku-deploy-tmp
```

### Smoke test plan (4 cases)

After dyno restart (~30 s — fewer files this time):

```
curl https://thammen.qa/api/health
# expected: engine_version = thammen-sprint2p18p1p1-compound-misroute-fix
```

Then `probe_compound_classifier_bug.py` already includes the 3 relevant cases:
1. 51/835/17 — must flip to `valuation=None`
2. PIN 66030258 — must stay at `valuation=None` (unchanged)
3. 69/112/36 — must stay at `valuation=None` (unchanged fast-path)

Plus the multi_qars_56 regression check via direct curl (must still produce valuation_amount with decomposition).

---

## 8. Decisions baked in (Anas, 2026-05-23 evening)

| # | decision | rationale |
|---|---|---|
| 1 | **2-tier (small ≤ 15 K, large > 15 K)** | Engine-level distinction has no actionable methodology difference today. UI uses existing compound_large terminology. |
| 2 | **Patch B (no COMPOUND_MEDIUM enum)** | Single-purpose Sprint per Rule #38. New enum has ripple effects through scope/brief/MUC/UI. |
| 3 | **Patch C universal** | Catches not just compound misroute but also premium-land villa teardowns + MoJ outliers. Protects against future bug classes in this family. |
| 4 | **Engine version `2.18.1.1`** | X.X.X.X hotfix pattern matches Sprint 2.21.0.7.1. Decimal-4 conveys "discovered-during-verification follow-up". |
| 5 | **CHANGELOG_v46.md (new)** | v45 ships as-is + gets a small post-deploy note (not retroactive edits). |
| 6 | **Probe verification post-deploy** | `probe_compound_classifier_bug.py` already exists from §5/C audit — just re-run. |

---

## 9. Roadmap context

| Sprint | Status | What |
|---|---|---|
| 2.18.0 | ✅ Heroku v99 | Parallel `property_factors` 5-layer fan-out. −4 s villa/raw_land. |
| 2.18.1 | ✅ Heroku v100 | Parallel `_expand_extent` BFS prefetch. −60 s compound_small. **Made the latent bug reachable.** |
| **2.18.1.1** | **this Sprint** | **Compound-misroute fix (Patches A + C). Closes the silent arithmetic failure on compound extents ≥ 15 K m².** |
| 2.18.2 (candidate) | Queued post-2.18.1.1 | Lite/full GIS-call dedup + boundary-test optimization. Targets the ~15 s Python overhead on compound_small. Would close Stage-1 (≤ 5 s) gap. |
| 2.21.0.10 (candidate) | Queued, conditional | Stage-2 wall-to-wall classification (E18). Conditional on Building Footprint layer probe. |
| 2.16.16 | Queued | Confirmed Sales DB integration. Awaiting secretary's data. |
| 2.21.1 | Queued | MME apartments. §21.6 smoke first. |

---

## 10. The unified narrative — Sprints 2.18.1 + 2.18.1.1

Sprint 2.18.1 successfully reduced latency on `compound_small` from 89 s to 29 s, converting HTTP 503×3 to HTTP 200×3. This was the user-visible deliverable as scoped. **But the verification step Anas runs after every deploy — visual inspection of the rendered report on thammen.qa — caught that the response now reaching the user contained a methodology bug that the prior 503 timeout had been masking.** Sprint 2.18.1's latency goal is fully delivered; user-facing completeness depended on closing the unmasked methodology bug. Sprint 2.18.1.1 does that.

Together, the two Sprints deliver one coherent change: **compound_small addresses are now reachable through the public API for the first time AND return methodologically correct output** (clean "insufficient_data: needs rent input" for compounds ≥ 15 K m², proper land+building decomposition for compounds < 15 K m²).

Session_Log §15 will cover both Sprints in a unified narrative once 2.18.1.1 ships and verifies.

---

*Sprint 2.18.1.1 closes a silent methodology bug class (`land > valuation` arithmetic failure) by promoting `compound_small` → `compound_large` when extent ≥ 15 K m² (Patch A) and adding a universal sanity guard in `_decompose_value` (Patch C). Discovered via post-deploy visual verification — the CLAUDE.md §3 pre-deploy checklist's last item ("smoke test 3 diverse addresses from Heroku post-deploy") working exactly as designed.*
